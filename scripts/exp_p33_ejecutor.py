#!/usr/bin/env python3
"""EXP P33 Ejecutor — Envía casos al Motor y guarda resultados."""

import httpx
import json
import asyncio
import os
import time
import glob
from datetime import datetime, timezone

BASE_URL = os.environ.get("P33_BASE_URL", "https://chief-os-omni.fly.dev")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "datos", "exp_p33")
CASOS_DIR = os.path.join(OUTPUT_DIR, "casos_input")
RESULTS_DIR = os.path.join(OUTPUT_DIR, "resultados")
TIMEOUT_S = 180


async def ejecutar_caso(client: httpx.AsyncClient, caso: dict) -> dict:
    """Envía un caso al Motor y registra resultado."""
    payload = {
        "input": caso["input"],
        "modo": "analisis",
        "consumidor": f"exp_p33:{caso['caso_id']}",
    }

    t0 = time.time()
    try:
        r = await client.post(f"{BASE_URL}/motor/ejecutar-vn", json=payload, timeout=TIMEOUT_S)
        t1 = time.time()

        if r.status_code == 200:
            resultado = r.json()
            return {
                "caso_id": caso["caso_id"],
                "status": "ok",
                "input_preview": caso["input"][:200],
                "response_raw": resultado,
                "inteligencias": resultado.get("inteligencias", []),
                "n_inteligencias": resultado.get("n_inteligencias", 0),
                "tier": resultado.get("tier", -1),
                "alpha": resultado.get("alpha", -1),
                "hallazgos": resultado.get("hallazgos", []),
                "n_hallazgos": len(resultado.get("hallazgos", [])),
                "sintesis": resultado.get("sintesis", ""),
                "señales_pid": resultado.get("señales_pid", []),
                "gradientes_top": resultado.get("gradientes_top", []),
                "metacognicion": resultado.get("metacognicion", {}),
                "metricas": resultado.get("metricas", {}),
                "coste_usd": resultado.get("metricas", {}).get("coste_usd", 0),
                "tiempo_s": t1 - t0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        else:
            return {
                "caso_id": caso["caso_id"],
                "status": "error",
                "http_status": r.status_code,
                "error": r.text[:500],
                "tiempo_s": time.time() - t0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
    except httpx.ReadTimeout:
        return {
            "caso_id": caso["caso_id"],
            "status": "timeout",
            "tiempo_s": time.time() - t0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {
            "caso_id": caso["caso_id"],
            "status": "error",
            "error": str(e)[:500],
            "tiempo_s": time.time() - t0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


async def main():
    # Load cases
    caso_files = sorted(glob.glob(os.path.join(CASOS_DIR, "p33_caso_*.json")))
    if not caso_files:
        print("[ejecutor] No se encontraron casos. Ejecuta primero exp_p33_recolector.py")
        return

    casos = []
    for f in caso_files:
        with open(f) as fh:
            casos.append(json.load(fh))
    print(f"[ejecutor] {len(casos)} casos cargados")

    # First: test probe to verify endpoint works
    print("[ejecutor] Probando endpoint con input mínimo...")
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(
                f"{BASE_URL}/motor/ejecutar-vn",
                json={"input": "test mínimo", "modo": "conversacion"},
                timeout=90,
            )
            if r.status_code == 200:
                probe = r.json()
                print(f"  → Probe OK: tier={probe.get('tier')}, keys={list(probe.keys())[:8]}")
            else:
                print(f"  → Probe FALLÓ: HTTP {r.status_code}")
                print(f"    {r.text[:300]}")
                return
        except Exception as e:
            print(f"  → Probe FALLÓ: {e}")
            return

    # Execute cases sequentially
    os.makedirs(RESULTS_DIR, exist_ok=True)
    resultados = []
    coste_total = 0

    async with httpx.AsyncClient() as client:
        for i, caso in enumerate(casos):
            print(f"\n[ejecutor] Caso {i+1}/{len(casos)}: {caso['caso_id']}")
            print(f"  Input: {caso['input'][:100]}...")

            resultado = await ejecutar_caso(client, caso)
            resultados.append(resultado)

            # Save individual result
            res_path = os.path.join(RESULTS_DIR, f"{caso['caso_id'].replace('caso', 'resultado')}.json")
            with open(res_path, "w") as f:
                json.dump(resultado, f, indent=2, ensure_ascii=False, default=str)

            if resultado["status"] == "ok":
                coste = resultado.get("coste_usd", 0)
                coste_total += coste
                print(f"  → OK: {resultado['n_inteligencias']} INTs, "
                      f"{resultado['n_hallazgos']} hallazgos, "
                      f"tier={resultado['tier']}, "
                      f"${coste:.4f}, "
                      f"{resultado['tiempo_s']:.1f}s")
            else:
                print(f"  → {resultado['status'].upper()}: {resultado.get('error', 'timeout')[:100]}")

            # Wait between cases to respect rate limits
            if i < len(casos) - 1:
                print("  Esperando 5s antes del siguiente caso...")
                await asyncio.sleep(5)

    # Summary
    ok = [r for r in resultados if r["status"] == "ok"]
    fails = [r for r in resultados if r["status"] != "ok"]
    print(f"\n[ejecutor] RESUMEN: {len(ok)}/{len(resultados)} OK, coste total ${coste_total:.4f}")
    if fails:
        print(f"  Fallos: {[f['caso_id'] + ':' + f['status'] for f in fails]}")

    # Save combined results
    combined_path = os.path.join(OUTPUT_DIR, "resultados_completos.json")
    with open(combined_path, "w") as f:
        json.dump({
            "total_casos": len(resultados),
            "ok": len(ok),
            "fallos": len(fails),
            "coste_total_usd": coste_total,
            "resultados": resultados,
        }, f, indent=2, ensure_ascii=False, default=str)
    print(f"[ejecutor] Resultados guardados en {combined_path}")

    return resultados


if __name__ == "__main__":
    asyncio.run(main())
