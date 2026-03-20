"""Smoke test E2E — Verifica todos los flujos del Exocortex Pilates.

Ejecutar: python scripts/smoke_test_e2e.py [BASE_URL]
Default: https://motor-semantico-omni.fly.dev
"""
import asyncio
import json
import sys
import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "https://motor-semantico-omni.fly.dev"
P = f"{BASE}/pilates"

PASS = 0
FAIL = 0
ERRORS = []


async def check(name: str, method: str, path: str, expected_status: int = 200,
                body: dict = None, check_fn=None):
    global PASS, FAIL
    url = f"{P}{path}"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            if method == "GET":
                r = await client.get(url)
            elif method == "POST":
                r = await client.post(url, json=body or {})
            elif method == "PATCH":
                r = await client.patch(url, json=body or {})
            else:
                r = await client.get(url)

            if r.status_code != expected_status:
                FAIL += 1
                ERRORS.append(f"FAIL {name}: expected {expected_status}, got {r.status_code}")
                print(f"  ❌ {name} — {r.status_code} (expected {expected_status})")
                return None

            data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}

            if check_fn and not check_fn(data):
                FAIL += 1
                ERRORS.append(f"FAIL {name}: check_fn failed")
                print(f"  ❌ {name} — check failed")
                return data

            PASS += 1
            print(f"  ✅ {name}")
            return data

    except Exception as e:
        FAIL += 1
        ERRORS.append(f"FAIL {name}: {str(e)[:100]}")
        print(f"  ❌ {name} — {str(e)[:80]}")
        return None


async def main():
    print(f"\n🔍 Smoke Test E2E — {BASE}\n")

    # ============ HEALTH ============
    print("=== HEALTH ===")
    await check("Health", "GET", "/../health")

    # ============ GRUPOS ============
    print("\n=== GRUPOS ===")
    grupos = await check("Listar grupos", "GET", "/grupos",
        check_fn=lambda d: len(d) >= 15)
    if grupos:
        g0 = grupos[0]
        await check("Detalle grupo", "GET", f"/grupos/{g0['id']}")
        await check("Agenda grupo", "GET", f"/grupos/{g0['id']}/agenda")

    # ============ CLIENTES ============
    print("\n=== CLIENTES ===")
    clientes = await check("Listar clientes", "GET", "/clientes",
        check_fn=lambda d: len(d) >= 1)
    await check("Buscar cliente", "GET", "/buscar?q=Maria")
    if clientes:
        c0 = clientes[0]
        await check("Detalle cliente", "GET", f"/clientes/{c0['id']}")

    # ============ CONTRATOS ============
    print("\n=== CONTRATOS ===")
    await check("Listar contratos", "GET", "/contratos",
        check_fn=lambda d: len(d) >= 1)

    # ============ SESIONES ============
    print("\n=== SESIONES ===")
    await check("Sesiones hoy", "GET", "/sesiones/hoy")

    # ============ CARGOS ============
    print("\n=== CARGOS ===")
    await check("Cargos pendientes", "GET", "/cargos?estado=pendiente")
    await check("Cargos cobrados", "GET", "/cargos?estado=cobrado")

    # ============ PAGOS ============
    print("\n=== PAGOS ===")
    await check("Listar pagos", "GET", "/pagos",
        check_fn=lambda d: len(d) >= 1)

    # ============ RESUMEN ============
    print("\n=== RESUMEN ===")
    resumen = await check("Resumen financiero", "GET", "/resumen",
        check_fn=lambda d: d.get("ingresos_mes", 0) >= 0)
    if resumen:
        print(f"     Ingresos: {resumen.get('ingresos_mes', 0):.0f}€, "
              f"Deuda: {resumen.get('deuda_pendiente', 0):.0f}€, "
              f"Ocupación: {resumen.get('ocupacion_pct', 0)}%")

    # ============ FACTURACIÓN ============
    print("\n=== FACTURACIÓN ===")
    await check("Listar facturas", "GET", "/facturas")
    paquete = await check("Paquete gestor", "GET", "/facturas/paquete-gestor")
    if paquete:
        print(f"     {paquete.get('trimestre', '?')}: "
              f"Ingresos {paquete.get('ingresos', {}).get('total', 0):.0f}€, "
              f"Gastos {paquete.get('gastos', {}).get('total', 0):.0f}€")

    # ============ WHATSAPP ============
    print("\n=== WHATSAPP ===")
    await check("Mensajes WA", "GET", "/whatsapp/mensajes")
    await check("Confirmar mañana", "POST", "/whatsapp/confirmar-manana")

    # ============ ONBOARDING ============
    print("\n=== ONBOARDING ===")
    await check("Enlaces onboarding", "GET", "/onboarding/enlaces")

    # ============ BRIEFING ============
    print("\n=== BRIEFING / DASHBOARD ===")
    briefing = await check("Briefing semanal", "GET", "/briefing")
    if briefing:
        n = briefing.get("numeros", {})
        print(f"     Asistencia: {n.get('asistencia_pct', 0)}%, "
              f"Clientes: {n.get('clientes_activos', 0)}")

    dashboard = await check("Dashboard profundo", "GET", "/dashboard")
    if dashboard and dashboard.get("grupos_detalle"):
        print(f"     {len(dashboard['grupos_detalle'])} grupos en dashboard")

    # ============ ACD ============
    print("\n=== ACD ===")
    await check("Historial ACD", "GET", "/acd/historial")

    # ============ CONSEJO ============
    print("\n=== SÉQUITO ===")
    await check("Listar asesores", "GET", "/asesores",
        check_fn=lambda d: len(d) == 24)
    await check("Historial consejo", "GET", "/consejo/historial")

    # ============ ADN ============
    print("\n=== ADN / PROCESOS / DEPURACIÓN ===")
    adn = await check("Listar ADN", "GET", "/adn")
    if adn:
        print(f"     {len(adn)} principios ADN")
    await check("Listar procesos", "GET", "/procesos")
    await check("Listar conocimiento", "GET", "/conocimiento")
    await check("Listar tensiones", "GET", "/tensiones")
    await check("Listar depuración", "GET", "/depuracion")
    await check("Readiness replicación", "GET", "/readiness")

    # ============ VOZ ============
    print("\n=== BLOQUE VOZ ===")
    await check("Propuestas voz", "GET", "/voz/propuestas")
    await check("Datos Capa A", "GET", "/voz/capa-a/datos")
    await check("Historial ISP", "GET", "/voz/isp")
    await check("Telemetría voz", "GET", "/voz/telemetria")

    # ============ ALERTAS ============
    print("\n=== ALERTAS / CRON ===")
    await check("Alertas retención", "GET", "/alertas")

    # ============ PORTAL ============
    print("\n=== PORTAL ===")
    await check("Generar portales", "POST", "/portal/generar-todos")

    # ============ RESUMEN FINAL ============
    print(f"\n{'='*50}")
    print(f"RESULTADO: {PASS} PASS / {FAIL} FAIL / {PASS+FAIL} TOTAL")
    if ERRORS:
        print(f"\nErrores:")
        for e in ERRORS:
            print(f"  {e}")
    print(f"{'='*50}\n")

    return FAIL == 0


if __name__ == "__main__":
    ok = asyncio.run(main())
    sys.exit(0 if ok else 1)
