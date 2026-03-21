# B-PIL-08: Facturación — Facturas + PDF + VeriFactu Ready + Paquete Gestor

**Fecha:** 2026-03-20
**Ejecutor:** Claude Code
**Dependencia:** B-PIL-04 (cargos/pagos operativos)
**Coste:** $0

---

## CONTEXTO

Los cargos y pagos funcionan. Ahora Jesús necesita emitir facturas. Las tablas `om_facturas` y `om_factura_lineas` ya existen (B-PIL-01). Falta:
1. Backend: crear facturas desde cargos cobrados, numerar secuencialmente, generar PDF
2. VeriFactu: cadena de hashes preparada (no activa hasta La Rioja ~2027)
3. Facturación aprendida: el sistema sabe quién pide factura y cuándo
4. Paquete trimestral gestor: descarga automática para la gestoría

**Fuente:** Exocortex v2.1 S1.6, S3 (T09-T10), S11, S13 (#12, #13).

---

## FASE A: Backend facturación en router.py

**Archivo:** `@project/src/pilates/router.py` — LEER PRIMERO. AÑADIR schemas + endpoints.

### Schemas

```python
class FacturaCreate(BaseModel):
    """Crear factura desde cargos cobrados de un cliente."""
    cliente_id: UUID
    cargo_ids: list[UUID]  # cargos a incluir en la factura
    fecha_operacion: Optional[date] = None

class FacturaAnular(BaseModel):
    motivo: str
```

### Endpoints (7 nuevos)

```python
# ============================================================
# FACTURACIÓN
# ============================================================

@router.post("/facturas", status_code=201)
async def crear_factura(data: FacturaCreate):
    """Crea factura desde cargos cobrados. Numera secuencialmente. VeriFactu ready.

    Serie: AP (Authentic Pilates). Numeración: AP-2026-0001, AP-2026-0002, ...
    Snapshot fiscal del cliente al momento de emisión.
    Hash SHA-256 encadenado (VeriFactu preparado, no activo).
    """
    import hashlib
    pool = await _get_pool()

    async with pool.acquire() as conn:
        async with conn.transaction():
            # Verificar cliente
            cliente = await conn.fetchrow(
                "SELECT * FROM om_clientes WHERE id = $1", data.cliente_id)
            if not cliente:
                raise HTTPException(404, "Cliente no encontrado")

            # Obtener cargos
            cargos = await conn.fetch("""
                SELECT * FROM om_cargos
                WHERE id = ANY($1::uuid[]) AND cliente_id = $2 AND tenant_id = $3
            """, data.cargo_ids, data.cliente_id, TENANT)
            if len(cargos) != len(data.cargo_ids):
                raise HTTPException(400, "Algunos cargos no encontrados o no pertenecen al cliente")

            # Calcular totales
            base_total = sum(float(c["base_imponible"]) for c in cargos)
            iva_pct = 21.00  # Pilates = 21% IVA
            iva_total = round(base_total * iva_pct / 100, 2)
            total = round(base_total + iva_total, 2)

            # Siguiente número de factura
            year = date.today().year
            serie = "AP"
            ultimo_num = await conn.fetchval("""
                SELECT MAX(CAST(SPLIT_PART(numero_factura, '-', 3) AS INT))
                FROM om_facturas
                WHERE tenant_id = $1 AND serie = $2
                    AND EXTRACT(YEAR FROM fecha_emision) = $3
            """, TENANT, serie, year)
            siguiente = (ultimo_num or 0) + 1
            numero = f"{serie}-{year}-{siguiente:04d}"

            # Hash VeriFactu (encadenado con factura anterior)
            hash_anterior = await conn.fetchval("""
                SELECT verifactu_hash FROM om_facturas
                WHERE tenant_id = $1 AND serie = $2
                ORDER BY created_at DESC LIMIT 1
            """, TENANT, serie)

            datos_hash = f"{numero}|{date.today()}|{total}|{hash_anterior or 'GENESIS'}"
            verifactu_hash = hashlib.sha256(datos_hash.encode()).hexdigest()

            # Crear factura con snapshot fiscal
            factura_row = await conn.fetchrow("""
                INSERT INTO om_facturas (
                    tenant_id, cliente_id, numero_factura, serie,
                    fecha_emision, fecha_operacion,
                    base_imponible, iva_porcentaje, iva_monto, total,
                    verifactu_hash, verifactu_hash_anterior,
                    cliente_nif, cliente_nombre_fiscal, cliente_direccion
                ) VALUES ($1,$2,$3,$4, CURRENT_DATE,$5, $6,$7,$8,$9, $10,$11, $12,$13,$14)
                RETURNING id
            """, TENANT, data.cliente_id, numero, serie,
                data.fecha_operacion,
                base_total, iva_pct, iva_total, total,
                verifactu_hash, hash_anterior,
                cliente["nif"],
                f"{cliente['nombre']} {cliente['apellidos']}",
                cliente["direccion"])

            factura_id = factura_row["id"]

            # Crear líneas de factura
            for cargo in cargos:
                bi = float(cargo["base_imponible"])
                iva_m = round(bi * iva_pct / 100, 2)
                await conn.execute("""
                    INSERT INTO om_factura_lineas (
                        factura_id, cargo_id, concepto, cantidad,
                        precio_unitario, base_imponible,
                        iva_porcentaje, iva_monto, total
                    ) VALUES ($1,$2,$3,1,$4,$5,$6,$7,$8)
                """, factura_id, cargo["id"],
                    cargo["descripcion"] or cargo["tipo"],
                    bi, bi, iva_pct, iva_m, round(bi + iva_m, 2))

    log.info("factura_creada", numero=numero, total=total, lineas=len(cargos))
    return {"id": str(factura_id), "numero": numero, "total": total, "status": "created"}


@router.get("/facturas")
async def listar_facturas(
    estado: Optional[str] = None,
    cliente_id: Optional[UUID] = None,
    year: Optional[int] = None,
    limit: int = 50
):
    """Lista facturas con filtros."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        conditions = ["f.tenant_id = $1"]
        params = [TENANT]
        idx = 2

        if estado:
            conditions.append(f"f.estado = ${idx}"); params.append(estado); idx += 1
        if cliente_id:
            conditions.append(f"f.cliente_id = ${idx}"); params.append(cliente_id); idx += 1
        if year:
            conditions.append(f"EXTRACT(YEAR FROM f.fecha_emision) = ${idx}"); params.append(year); idx += 1

        where = " AND ".join(conditions)
        rows = await conn.fetch(f"""
            SELECT f.*, cl.nombre, cl.apellidos
            FROM om_facturas f
            JOIN om_clientes cl ON cl.id = f.cliente_id
            WHERE {where}
            ORDER BY f.fecha_emision DESC, f.numero_factura DESC
            LIMIT ${idx}
        """, *params, limit)
    return [_row_to_dict(r) for r in rows]


@router.get("/facturas/{factura_id}")
async def obtener_factura(factura_id: UUID):
    """Detalle de factura con líneas."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        factura = await conn.fetchrow(
            "SELECT * FROM om_facturas WHERE id = $1 AND tenant_id = $2",
            factura_id, TENANT)
        if not factura:
            raise HTTPException(404, "Factura no encontrada")

        lineas = await conn.fetch("""
            SELECT * FROM om_factura_lineas WHERE factura_id = $1 ORDER BY created_at
        """, factura_id)

        cliente = await conn.fetchrow(
            "SELECT * FROM om_clientes WHERE id = $1", factura["cliente_id"])

    return {
        **_row_to_dict(factura),
        "lineas": [_row_to_dict(l) for l in lineas],
        "cliente": _row_to_dict(cliente) if cliente else None,
    }


@router.post("/facturas/{factura_id}/anular")
async def anular_factura(factura_id: UUID, data: FacturaAnular):
    """Anula factura. No se borra — se marca como anulada (VeriFactu)."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("""
            UPDATE om_facturas SET estado = 'anulada'
            WHERE id = $1 AND tenant_id = $2 AND estado = 'emitida'
        """, factura_id, TENANT)
        if result == "UPDATE 0":
            raise HTTPException(404, "Factura no encontrada o ya anulada")

    log.info("factura_anulada", id=str(factura_id), motivo=data.motivo)
    return {"status": "anulada"}


@router.post("/facturas/{factura_id}/pdf")
async def generar_pdf_factura(factura_id: UUID):
    """Genera PDF de la factura. Devuelve path del archivo.

    Usa weasyprint o reportlab. Formato: datos fiscales emisor + receptor,
    tabla de líneas, totales, hash VeriFactu.
    """
    pool = await _get_pool()
    async with pool.acquire() as conn:
        factura = await conn.fetchrow(
            "SELECT * FROM om_facturas WHERE id = $1 AND tenant_id = $2",
            factura_id, TENANT)
        if not factura:
            raise HTTPException(404, "Factura no encontrada")

        lineas = await conn.fetch(
            "SELECT * FROM om_factura_lineas WHERE factura_id = $1", factura_id)

    # Generar HTML de la factura
    html = _generar_html_factura(factura, lineas)

    # Intentar generar PDF con weasyprint
    try:
        from weasyprint import HTML
        import tempfile, os
        pdf_filename = f"factura_{factura['numero_factura'].replace('-','_')}.pdf"
        pdf_path = f"/tmp/{pdf_filename}"
        HTML(string=html).write_pdf(pdf_path)

        # Guardar path en DB
        await pool.acquire() as conn2:
            await conn2.execute(
                "UPDATE om_facturas SET pdf_path = $1 WHERE id = $2",
                pdf_path, factura_id)

        return {"status": "ok", "pdf_path": pdf_path, "filename": pdf_filename}
    except ImportError:
        # Si weasyprint no está, devolver HTML para que el frontend lo renderice
        return {"status": "html_only", "html": html,
                "nota": "Instalar weasyprint en requirements.txt para PDF nativo"}


@router.post("/facturas/auto-facturar")
async def auto_facturar():
    """Facturación automática para clientes que siempre piden factura.

    Busca cargos cobrados sin factura para clientes con preferencia 'siempre'.
    Genera facturas automáticamente.
    """
    pool = await _get_pool()
    facturas_creadas = 0

    async with pool.acquire() as conn:
        # Clientes con facturación aprendida = siempre
        # (campo metodo_pago_habitual reutilizado; en v2 será campo dedicado)
        # Por ahora: buscar cargos cobrados sin factura asociada
        clientes_con_cargos = await conn.fetch("""
            SELECT DISTINCT c.cliente_id, cl.nombre, cl.apellidos
            FROM om_cargos c
            JOIN om_clientes cl ON cl.id = c.cliente_id
            LEFT JOIN om_factura_lineas fl ON fl.cargo_id = c.id
            WHERE c.tenant_id = $1 AND c.estado = 'cobrado' AND fl.id IS NULL
            GROUP BY c.cliente_id, cl.nombre, cl.apellidos
        """, TENANT)

        # Por ahora solo lista los candidatos — la auto-facturación
        # se activará cuando haya preferencia explícita por cliente

    return {
        "status": "ok",
        "clientes_con_cargos_sin_factura": len(clientes_con_cargos),
        "clientes": [{"id": str(c["cliente_id"]),
                       "nombre": f"{c['nombre']} {c['apellidos']}"}
                      for c in clientes_con_cargos],
        "nota": "Auto-facturación pendiente de campo preferencia_facturacion en om_clientes"
    }


@router.get("/facturas/paquete-gestor")
async def paquete_gestor(trimestre: Optional[int] = None, year: Optional[int] = None):
    """Resumen trimestral para la gestoría.

    Devuelve: facturas emitidas, IVA repercutido, gastos, IVA soportado,
    IVA a liquidar, resumen por tipo.
    """
    import calendar
    year = year or date.today().year
    if trimestre is None:
        trimestre = (date.today().month - 1) // 3 + 1

    mes_inicio = (trimestre - 1) * 3 + 1
    mes_fin = trimestre * 3
    fecha_inicio = date(year, mes_inicio, 1)
    fecha_fin = date(year, mes_fin, calendar.monthrange(year, mes_fin)[1])

    pool = await _get_pool()
    async with pool.acquire() as conn:
        # Facturas emitidas
        facturas = await conn.fetch("""
            SELECT * FROM om_facturas
            WHERE tenant_id = $1 AND fecha_emision >= $2 AND fecha_emision <= $3
                AND estado = 'emitida'
            ORDER BY numero_factura
        """, TENANT, fecha_inicio, fecha_fin)

        iva_repercutido = sum(float(f["iva_monto"]) for f in facturas)
        base_ingresos = sum(float(f["base_imponible"]) for f in facturas)
        total_ingresos = sum(float(f["total"]) for f in facturas)

        # Gastos del trimestre
        gastos = await conn.fetch("""
            SELECT * FROM om_gastos
            WHERE tenant_id = $1 AND fecha_gasto >= $2 AND fecha_gasto <= $3
            ORDER BY fecha_gasto
        """, TENANT, fecha_inicio, fecha_fin)

        iva_soportado = sum(float(g["iva_soportado"] or 0) for g in gastos)
        base_gastos = sum(float(g["base_imponible"]) for g in gastos)
        total_gastos = sum(float(g["total"]) for g in gastos)

        # Gastos por categoría
        gastos_por_cat = {}
        for g in gastos:
            cat = g["categoria"]
            gastos_por_cat[cat] = gastos_por_cat.get(cat, 0) + float(g["total"])

    return {
        "trimestre": f"Q{trimestre} {year}",
        "periodo": f"{fecha_inicio} a {fecha_fin}",
        "ingresos": {
            "facturas_emitidas": len(facturas),
            "base_imponible": round(base_ingresos, 2),
            "iva_repercutido": round(iva_repercutido, 2),
            "total": round(total_ingresos, 2),
        },
        "gastos": {
            "total_gastos": len(gastos),
            "base_imponible": round(base_gastos, 2),
            "iva_soportado": round(iva_soportado, 2),
            "total": round(total_gastos, 2),
            "por_categoria": gastos_por_cat,
        },
        "iva_liquidar": round(iva_repercutido - iva_soportado, 2),
        "resultado_neto": round(base_ingresos - base_gastos, 2),
    }
```

### Helper: HTML de factura

AÑADIR como función privada en router.py (fuera de los endpoints):

```python
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
      Jesús Fernández Domínguez<br>
      Logroño, La Rioja<br>
      <!-- NIF PENDIENTE -->
    </div>
  </div>

  <div class="receptor">
    <strong>Cliente:</strong> {factura['cliente_nombre_fiscal'] or 'Sin datos fiscales'}<br>
    {f"NIF: {factura['cliente_nif']}<br>" if factura['cliente_nif'] else ''}
    {f"Dirección: {factura['cliente_direccion']}" if factura['cliente_direccion'] else ''}
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
```

---

## FASE B: Dependencia weasyprint (opcional)

**Archivo:** `@project/requirements.txt` — AÑADIR (opcional, para PDF nativo):

```
weasyprint>=60.0
```

**Nota:** weasyprint requiere cairo/pango en el sistema. En fly.io Dockerfile añadir:

```dockerfile
RUN apt-get update && apt-get install -y libcairo2 libpango-1.0-0 libpangocairo-1.0-0 && rm -rf /var/lib/apt/lists/*
```

Si no se instala, el endpoint `/facturas/{id}/pdf` devuelve HTML que el frontend puede renderizar con `window.print()`.

---

## FASE C: Integrar en frontend Modo Estudio

### C1. En api.js añadir:

```javascript
export const crearFactura = (data) => request('/facturas', { method: 'POST', body: JSON.stringify(data) });
export const getFacturas = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/facturas${qs ? `?${qs}` : ''}`);
};
export const getFactura = (id) => request(`/facturas/${id}`);
export const generarPdfFactura = (id) => request(`/facturas/${id}/pdf`, { method: 'POST' });
export const getPaqueteGestor = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/facturas/paquete-gestor${qs ? `?${qs}` : ''}`);
};
```

### C2. En el modal de cobro (App.jsx), después de cobrar exitosamente, ofrecer generar factura:

```jsx
// Después del toast.success del cobro:
if (window.confirm('¿Generar factura?')) {
  const cargoIds = cargosPendientes.map(c => c.id);
  await api.crearFactura({ cliente_id: clienteId, cargo_ids: cargoIds });
  toast.success('Factura generada');
}
```

---

## FASE D: Migración — añadir preferencia facturación a om_clientes

**Archivo:** `@project/migrations/om_add_pref_facturacion.sql`

```sql
-- Añade preferencia de facturación aprendida por cliente
ALTER TABLE om_clientes ADD COLUMN IF NOT EXISTS
    preferencia_facturacion TEXT DEFAULT 'nunca'
    CHECK (preferencia_facturacion IN ('siempre', 'trimestral', 'esporadica', 'nunca'));
```

Esto permite que auto-facturar filtre por clientes con preferencia='siempre'.

---

## Pass/fail

- POST /pilates/facturas crea factura con número secuencial (AP-2026-0001)
- Factura incluye snapshot fiscal del cliente (NIF, nombre, dirección)
- Hash VeriFactu encadenado (SHA-256, cada factura referencia la anterior)
- GET /pilates/facturas lista con filtros (estado, cliente, año)
- GET /pilates/facturas/{id} devuelve detalle con líneas
- POST /pilates/facturas/{id}/anular marca como anulada (no borra)
- POST /pilates/facturas/{id}/pdf genera HTML (PDF si weasyprint instalado)
- GET /pilates/facturas/paquete-gestor devuelve resumen trimestral completo
- POST /pilates/facturas/auto-facturar lista candidatos (auto real pendiente preferencia)
- Migration añade preferencia_facturacion a om_clientes
- ~29 endpoints Pilates totales

---

## NOTAS

- **Serie AP** = Authentic Pilates. Si se crea SL, cambiar serie
- **VeriFactu no activo** — La Rioja ~2027. El hash encadenado está preparado pero no se envía a Hacienda
- **PENDIENTE forma jurídica** — afecta datos fiscales del emisor en la factura. Por ahora sin NIF emisor
- **weasyprint opcional** — sin él, el endpoint devuelve HTML para `window.print()` del navegador
- **Paquete gestor** incluye: facturas emitidas, IVA repercutido/soportado, gastos por categoría, IVA a liquidar, resultado neto. Es lo que Jesús envía a su gestor cada trimestre
