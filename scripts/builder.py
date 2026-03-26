#!/usr/bin/env python3
"""Agente Builder — Segundo agente de la fábrica OMNI-MIND.

Lee hallazgos del Verificador, genera fixes con Claude, los aplica y deploya.
Trabaja en loop con el Verificador: fix → deploy → verify → fix → ...

Uso:
  python3 scripts/builder.py                    # Fix el hallazgo más crítico
  python3 scripts/builder.py --all              # Fix todos los hallazgos
  python3 scripts/builder.py --dry-run          # Genera fix sin aplicar
  python3 scripts/builder.py --loop 3           # 3 ciclos Verificador→Builder
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx
from dotenv import load_dotenv

# URL base del motor en fly.io
FLY_APP_NAME = "motor-semantico-omni"
MOTOR_BASE_URL = os.getenv("MOTOR_BASE_URL", f"https://{FLY_APP_NAME}.fly.dev")

load_dotenv()

ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY_1", os.getenv("ANTHROPIC_API_KEY", ""))
MOTOR_DIR = Path(__file__).parent.parent
SRC_DIR = MOTOR_DIR / "src"

# ============================================================
# LLM
# ============================================================

async def llamar_claude(system: str, user: str, model: str = "claude-sonnet-4-20250514") -> str:
    """Una llamada a Claude. Devuelve texto."""
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": model,
                "max_tokens": 4096,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
        )
        data = r.json()
        return data.get("content", [{}])[0].get("text", "")


# ============================================================
# LEER HALLAZGOS DEL VERIFICADOR
# ============================================================

def leer_hallazgos_ultimo_run() -> list[dict]:
    """Lee hallazgos del último run del verificador (desde stdout JSON)."""
    # Ejecutar verificador y capturar output
    result = subprocess.run(
        [sys.executable, str(MOTOR_DIR / "scripts" / "verificador.py"), "--dry-run"],
        capture_output=True, text=True, cwd=str(MOTOR_DIR),
        env={**os.environ},
        timeout=120,
    )

    hallazgos = []
    output = result.stdout

    # Parsear hallazgos del output
    # Buscar líneas con 💥 (500 errors) o ❌ (errores)
    for line in output.split("\n"):
        if "💥" in line:
            # Extraer endpoint y status
            match = re.search(r"(/.+?)\s+→\s+(\d+)", line)
            if match:
                hallazgos.append({
                    "severidad": "critical",
                    "endpoint": match.group(1),
                    "titulo": f"Error {match.group(2)} en {match.group(1)}",
                    "descripcion": line.strip(),
                })
        elif "❌" in line and "→" in line:
            match = re.search(r"(/.+?)\s+→\s+(\d+)", line)
            if match:
                hallazgos.append({
                    "severidad": "major",
                    "endpoint": match.group(1),
                    "titulo": f"Error en {match.group(1)}",
                    "descripcion": line.strip(),
                })

    # Parsear JSON del dry-run
    json_match = re.search(r'\{[^}]*"verificacion_id"[^}]*\}', output, re.DOTALL)
    if json_match:
        try:
            run_data = json.loads(json_match.group())
            llm_data = run_data.get("llm")
            if llm_data and isinstance(llm_data, dict):
                for prio in llm_data.get("top_3_prioridades", []):
                    # Evitar duplicados
                    if not any(h["titulo"] in prio or prio in h.get("descripcion", "") for h in hallazgos):
                        hallazgos.append({
                            "severidad": "major",
                            "endpoint": "",
                            "titulo": prio,
                            "descripcion": f"Prioridad del LLM: {prio}",
                        })
        except json.JSONDecodeError:
            pass

    return hallazgos


# ============================================================
# LEER LOGS DE FLY.IO
# ============================================================

def leer_logs_fly(filtro: str = "") -> str:
    """Lee logs recientes de fly.io buscando errores relevantes."""
    try:
        result = subprocess.run(
            ["fly", "logs", "-a", FLY_APP_NAME, "--no-tail"],
            capture_output=True, text=True, cwd=str(MOTOR_DIR),
            timeout=30,
        )
        if result.returncode != 0:
            return f"[No se pudieron leer logs: {result.stderr[:200]}]"

        # Filtrar líneas relevantes a errores
        lines = result.stdout.split("\n")
        error_lines = []
        for i, line in enumerate(lines):
            lowered = line.lower()
            if any(kw in lowered for kw in ["error", "traceback", "exception", "does not exist", "500", "failed"]):
                # Incluir 2 líneas antes y 5 después para contexto
                start = max(0, i - 2)
                end = min(len(lines), i + 6)
                chunk = lines[start:end]
                error_lines.extend(chunk)
                error_lines.append("---")

        if not error_lines:
            return "[No se encontraron errores en los logs recientes]"

        # Deduplicar y limitar
        seen = set()
        unique = []
        for line in error_lines:
            if line not in seen:
                seen.add(line)
                unique.append(line)

        return "\n".join(unique[-40:])  # Últimas 40 líneas únicas
    except subprocess.TimeoutExpired:
        return "[Timeout leyendo logs de fly.io]"
    except FileNotFoundError:
        return "[fly CLI no encontrado — instalar flyctl]"


# ============================================================
# GIT STASH — SAFETY
# ============================================================

def git_stash_save() -> bool:
    """Guarda cambios actuales en git stash antes de aplicar fixes."""
    result = subprocess.run(
        ["git", "stash", "push", "-m", f"builder-safety-{int(time.time())}"],
        cwd=str(MOTOR_DIR),
        capture_output=True, text=True,
        timeout=15,
    )
    stashed = "No local changes" not in result.stdout
    if stashed:
        print("  🔒 git stash guardado (safety backup)")
    else:
        print("  ℹ️ No hay cambios previos para guardar en stash")
    return stashed


def git_stash_pop() -> bool:
    """Restaura el último stash (rollback)."""
    result = subprocess.run(
        ["git", "stash", "pop"],
        cwd=str(MOTOR_DIR),
        capture_output=True, text=True,
        timeout=15,
    )
    if result.returncode == 0:
        print("  🔄 git stash pop — rollback aplicado")
        return True
    else:
        print(f"  ⚠️ git stash pop falló: {result.stderr[:200]}")
        return False


# ============================================================
# VERIFICAR ENDPOINT POST-DEPLOY
# ============================================================

async def verificar_endpoint_post_deploy(endpoint: str) -> bool:
    """Hace curl al endpoint afectado para verificar que el fix funcionó."""
    if not endpoint:
        print("  ⚠️ Sin endpoint para verificar post-deploy")
        return True  # No bloquear si no hay endpoint

    url = f"{MOTOR_BASE_URL}{endpoint}"
    print(f"  🔍 Verificando post-deploy: {url}")

    # Esperar un momento para que el deploy se estabilice
    await asyncio.sleep(5)

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url)
            if r.status_code < 500:
                print(f"  ✅ Verificación OK — {r.status_code}")
                return True
            else:
                print(f"  ❌ Verificación FALLO — {r.status_code}")
                return False
    except Exception as e:
        print(f"  ⚠️ Verificación falló (network): {e}")
        return False


# ============================================================
# ENCONTRAR ARCHIVO RESPONSABLE
# ============================================================

def encontrar_archivo_responsable(endpoint: str) -> tuple[Optional[Path], list[Path]]:
    """Busca qué archivo Python implementa un endpoint dado.

    Devuelve: (archivo_router, [archivos_relacionados])
    """
    if not endpoint:
        return None, []

    # Normalizar: /pilates/predicciones → predicciones
    parts = endpoint.strip("/").split("/")
    search_term = parts[-1] if parts else ""

    router_file = None
    related = []

    # Buscar en TODOS los .py del proyecto
    for py_file in MOTOR_DIR.rglob("*.py"):
        if "__pycache__" in str(py_file) or "node_modules" in str(py_file):
            continue
        try:
            content = py_file.read_text()
            # Match exacto del path en decorador
            if f'"/{search_term}"' in content and "@router" in content:
                router_file = py_file
            elif f"'/{search_term}'" in content and "@router" in content:
                router_file = py_file
            # Match en imports o funciones relacionadas
            elif search_term in content and ("def " in content or "import" in content):
                related.append(py_file)
        except Exception:
            continue

    return router_file, related[:3]  # Max 3 archivos relacionados


def leer_archivo(path: Path) -> str:
    """Lee un archivo y devuelve su contenido."""
    try:
        return path.read_text()
    except Exception:
        return ""


# ============================================================
# GENERAR FIX
# ============================================================

async def generar_fix(hallazgo: dict, dry_run: bool = False) -> Optional[dict]:
    """Usa Claude Sonnet para generar un fix para el hallazgo."""
    if not ANTHROPIC_KEY:
        print("  ❌ Sin ANTHROPIC_API_KEY, no puedo generar fix")
        return None

    endpoint = hallazgo.get("endpoint", "")
    archivo, relacionados = encontrar_archivo_responsable(endpoint)

    context_code = ""
    if archivo:
        context_code = f"\n\nARCHIVO ROUTER: {archivo.relative_to(MOTOR_DIR)}\n```python\n{leer_archivo(archivo)[:4000]}\n```"
    for rel in relacionados[:2]:
        try:
            context_code += f"\n\nARCHIVO RELACIONADO: {rel.relative_to(MOTOR_DIR)}\n```python\n{leer_archivo(rel)[:3000]}\n```"
        except Exception:
            pass

    # Leer logs de fly.io si el hallazgo es un error 500
    fly_logs_context = ""
    if hallazgo.get("severidad") == "critical" or "500" in hallazgo.get("titulo", ""):
        print("  📡 Leyendo logs de fly.io para contexto...")
        fly_logs = leer_logs_fly()
        if fly_logs and "[No se" not in fly_logs:
            fly_logs_context = f"\n\nLOGS DE PRODUCCIÓN (fly.io):\n```\n{fly_logs}\n```"
            print(f"  📡 {len(fly_logs.splitlines())} líneas de logs obtenidas")
        else:
            print(f"  📡 {fly_logs}")

    system = """Eres un ingeniero senior arreglando bugs en un SaaS de gestión para estudios de Pilates.
Stack: Python 3.12 + FastAPI + asyncpg + PostgreSQL.

REGLAS:
1. Genera SOLO el código mínimo para arreglar el problema
2. No añadas features nuevas
3. No cambies la estructura del proyecto
4. Presta MÁXIMA atención a los LOGS DE PRODUCCIÓN si están presentes — contienen el error real (traceback, excepción, tabla/columna que falta, etc.)
5. Responde en JSON con este formato exacto:
{
  "archivo": "ruta/relativa/al/archivo.py",
  "tipo": "edit" | "create",
  "buscar": "texto exacto a reemplazar (solo para edit)",
  "reemplazar": "texto nuevo",
  "explicacion": "1 frase de qué arregla"
}

Si necesitas múltiples cambios, devuelve un JSON array de objetos."""

    user = f"""HALLAZGO: {hallazgo['titulo']}
SEVERIDAD: {hallazgo['severidad']}
DESCRIPCIÓN: {hallazgo['descripcion']}
ENDPOINT: {endpoint}
{context_code}
{fly_logs_context}

Genera el fix mínimo. Si hay logs de producción, usa el error EXACTO de los logs para guiar tu fix."""

    print(f"  🤖 Generando fix con Claude Sonnet...")
    response = await llamar_claude(system, user)

    # Parsear JSON de la respuesta (manejar markdown code blocks)
    clean = response
    # Quitar ```json ... ```
    if "```json" in clean:
        clean = clean.split("```json", 1)[1]
        if "```" in clean:
            clean = clean.split("```", 1)[0]
    elif "```" in clean:
        parts = clean.split("```")
        if len(parts) >= 3:
            clean = parts[1]

    try:
        start = clean.find("[") if "[" in clean else clean.find("{")
        end = clean.rfind("]") + 1 if "[" in clean else clean.rfind("}") + 1
        if start >= 0 and end > start:
            fixes = json.loads(clean[start:end])
            if isinstance(fixes, dict):
                fixes = [fixes]
            return fixes
    except json.JSONDecodeError:
        print(f"  ⚠️ No pudo parsear JSON del fix")
        print(f"  Raw: {clean[:300]}")

    return None


# ============================================================
# APLICAR FIX
# ============================================================

def aplicar_fix(fix: dict, dry_run: bool = False) -> bool:
    """Aplica un fix al código. Devuelve True si tuvo éxito."""
    archivo = MOTOR_DIR / fix.get("archivo", "")
    tipo = fix.get("tipo", "edit")
    explicacion = fix.get("explicacion", "")

    print(f"  📝 {explicacion}")
    print(f"     Archivo: {fix.get('archivo', '?')}")

    if dry_run:
        print(f"     [DRY RUN] No se aplica")
        return True

    if tipo == "create":
        # Crear archivo nuevo
        archivo.parent.mkdir(parents=True, exist_ok=True)
        archivo.write_text(fix.get("reemplazar", ""))
        print(f"     ✅ Archivo creado")
        return True

    elif tipo == "edit":
        buscar = fix.get("buscar", "")
        reemplazar = fix.get("reemplazar", "")

        if not archivo.exists():
            print(f"     ❌ Archivo no existe: {archivo}")
            return False

        contenido = archivo.read_text()
        if buscar not in contenido:
            print(f"     ❌ Texto a buscar no encontrado")
            print(f"     Buscando: {buscar[:100]}...")
            return False

        nuevo = contenido.replace(buscar, reemplazar, 1)
        archivo.write_text(nuevo)
        print(f"     ✅ Fix aplicado")
        return True

    return False


# ============================================================
# DEPLOY
# ============================================================

def deploy() -> bool:
    """Deploy a fly.io."""
    print("\n🚀 Desplegando a producción...")
    result = subprocess.run(
        ["fly", "deploy", "--remote-only"],
        cwd=str(MOTOR_DIR),
        capture_output=True, text=True,
        timeout=300,
    )
    if result.returncode == 0:
        print("  ✅ Deploy exitoso")
        return True
    else:
        print(f"  ❌ Deploy falló: {result.stderr[-500:]}")
        return False


# ============================================================
# LOOP PRINCIPAL
# ============================================================

async def run_once(dry_run: bool = False, fix_all: bool = False) -> dict:
    """Un ciclo: leer hallazgos → generar fixes → aplicar → deploy."""
    print("=" * 60)
    print("  AGENTE BUILDER — Fábrica OMNI-MIND")
    print(f"  Modo: {'DRY RUN' if dry_run else 'PRODUCCIÓN'}")
    print("=" * 60)

    # 1. Leer hallazgos
    print("\n📋 Leyendo hallazgos del Verificador...")
    hallazgos = leer_hallazgos_ultimo_run()

    if not hallazgos:
        print("  ✅ 0 hallazgos — nada que arreglar")
        return {"fixes_applied": 0, "hallazgos": 0}

    # Ordenar por severidad
    sev_order = {"blocker": 0, "critical": 1, "major": 2, "minor": 3, "cosmetic": 4}
    hallazgos.sort(key=lambda h: sev_order.get(h.get("severidad", "minor"), 3))

    if not fix_all:
        hallazgos = hallazgos[:1]  # Solo el más crítico

    print(f"  Hallazgos a procesar: {len(hallazgos)}")
    for h in hallazgos:
        print(f"    [{h['severidad'].upper()}] {h['titulo']}")

    # 2. Safety: git stash antes de tocar código
    stashed = False
    if not dry_run:
        stashed = git_stash_save()

    # 3. Generar y aplicar fixes
    fixes_applied = 0
    endpoints_afectados = []
    for i, hallazgo in enumerate(hallazgos, 1):
        print(f"\n{'─' * 40}")
        print(f"  FIX {i}/{len(hallazgos)}: {hallazgo['titulo']}")
        print(f"{'─' * 40}")

        fixes = await generar_fix(hallazgo, dry_run)
        if not fixes:
            print(f"  ⚠️ No se pudo generar fix")
            continue

        for fix in fixes:
            if aplicar_fix(fix, dry_run):
                fixes_applied += 1

        if hallazgo.get("endpoint"):
            endpoints_afectados.append(hallazgo["endpoint"])

    # 4. Deploy si hubo cambios
    deploy_ok = False
    if fixes_applied > 0 and not dry_run:
        deploy_ok = deploy()

        if not deploy_ok:
            # Deploy falló — rollback con git stash pop
            print("\n  ⚠️ Deploy falló — ejecutando rollback...")
            if stashed:
                git_stash_pop()
            else:
                # Revertir cambios del working tree
                subprocess.run(
                    ["git", "checkout", "--", "."],
                    cwd=str(MOTOR_DIR),
                    capture_output=True, text=True, timeout=15,
                )
                print("  🔄 git checkout -- . — cambios revertidos")
        else:
            # 5. Verificar endpoints post-deploy
            verificaciones_ok = 0
            verificaciones_total = len(endpoints_afectados)
            for ep in endpoints_afectados:
                if await verificar_endpoint_post_deploy(ep):
                    verificaciones_ok += 1

            if verificaciones_total > 0:
                print(f"\n  📊 Verificación post-deploy: {verificaciones_ok}/{verificaciones_total} endpoints OK")
                if verificaciones_ok < verificaciones_total:
                    print("  ⚠️ Algunos endpoints siguen fallando — revisar manualmente")

    print(f"\n{'=' * 60}")
    print(f"  RESULTADO BUILDER")
    print(f"  Hallazgos procesados: {len(hallazgos)}")
    print(f"  Fixes aplicados: {fixes_applied}")
    if not dry_run and fixes_applied > 0:
        print(f"  Deploy: {'OK' if deploy_ok else 'FALLIDO (rollback)'}")
    print(f"{'=' * 60}")

    return {"fixes_applied": fixes_applied, "hallazgos": len(hallazgos), "deploy_ok": deploy_ok if not dry_run else None}


async def run_loop(cycles: int, dry_run: bool = False):
    """Loop: Verificador → Builder → Deploy → Verificador → ..."""
    print(f"\n🔄 LOOP FÁBRICA — {cycles} ciclos")
    print("=" * 60)

    for cycle in range(1, cycles + 1):
        print(f"\n{'━' * 60}")
        print(f"  CICLO {cycle}/{cycles}")
        print(f"{'━' * 60}")

        result = await run_once(dry_run=dry_run, fix_all=False)

        if result["fixes_applied"] == 0:
            print(f"\n  ✅ Sin más fixes — fábrica se detiene en ciclo {cycle}")
            break

        if cycle < cycles and not dry_run:
            print(f"\n  ⏳ Esperando 30s para que el deploy se estabilice...")
            await asyncio.sleep(30)

    print(f"\n{'━' * 60}")
    print(f"  FÁBRICA COMPLETADA — {cycle} ciclos ejecutados")
    print(f"{'━' * 60}")


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Agente Builder OMNI-MIND")
    parser.add_argument("--dry-run", action="store_true", help="Genera fixes sin aplicar")
    parser.add_argument("--all", action="store_true", help="Fix todos los hallazgos")
    parser.add_argument("--loop", type=int, default=0,
                        help="Ejecutar N ciclos Verificador→Builder")
    args = parser.parse_args()

    if not ANTHROPIC_KEY:
        print("❌ ANTHROPIC_API_KEY_1 no configurada en .env")
        sys.exit(1)

    if args.loop > 0:
        asyncio.run(run_loop(args.loop, dry_run=args.dry_run))
    else:
        asyncio.run(run_once(dry_run=args.dry_run, fix_all=args.all))


if __name__ == "__main__":
    main()
