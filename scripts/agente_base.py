"""Base compartida para todos los agentes de la fabrica OMNI-MIND.

Cada agente hereda de AgenteBase e implementa:
  - ejecutar_tarea(tarea) → resultado
  - generar_tareas() → lista de tareas nuevas (opcional)

Comunicacion entre agentes: SOLO via archivos en tasks/ y reports/
  - Un agente deja una tarea en tasks/<destino>/
  - El agente destino la lee, ejecuta, y deja resultado en reports/
"""
from __future__ import annotations

import asyncio
import json
import os
import time
import yaml
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

MOTOR_DIR = Path(__file__).parent.parent
TASKS_DIR = MOTOR_DIR / "tasks"
REPORTS_DIR = MOTOR_DIR / "reports"
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY_1", os.getenv("ANTHROPIC_API_KEY", ""))


async def llamar_llm(system: str, user: str, model: str = "claude-sonnet-4-20250514",
                     max_tokens: int = 4096) -> str:
    """Llamada a Claude. Devuelve texto."""
    if not ANTHROPIC_KEY:
        return "[ERROR: Sin ANTHROPIC_API_KEY]"
    async with httpx.AsyncClient(timeout=90) as client:
        r = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": model,
                "max_tokens": max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
        )
        data = r.json()
        return data.get("content", [{}])[0].get("text", "")


def leer_tareas_pendientes(agente: str) -> list[dict]:
    """Lee tareas pendientes para un agente desde tasks/<agente>/."""
    carpeta = TASKS_DIR / agente
    carpeta.mkdir(parents=True, exist_ok=True)
    tareas = []
    for f in sorted(carpeta.glob("*.yaml")):
        try:
            data = yaml.safe_load(f.read_text())
            if data and data.get("estado", "pendiente") == "pendiente":
                data["_archivo"] = str(f)
                tareas.append(data)
        except Exception:
            continue
    # Ordenar por prioridad (1=max)
    tareas.sort(key=lambda t: t.get("prioridad", 5))
    return tareas


def marcar_tarea(archivo: str, estado: str, resultado: dict = None):
    """Marca una tarea como completada/fallida."""
    path = Path(archivo)
    if not path.exists():
        return
    data = yaml.safe_load(path.read_text()) or {}
    data["estado"] = estado
    data["completada_at"] = datetime.now().isoformat()
    if resultado:
        data["resultado"] = resultado
    path.write_text(yaml.dump(data, allow_unicode=True, default_flow_style=False))


def crear_tarea(destino: str, tarea: dict):
    """Crea una tarea nueva para otro agente (estigmergia via archivos)."""
    carpeta = TASKS_DIR / destino
    carpeta.mkdir(parents=True, exist_ok=True)
    ts = int(time.time() * 1000)
    nombre = f"{ts}_{tarea.get('tipo', 'tarea')}.yaml"
    tarea.setdefault("estado", "pendiente")
    tarea.setdefault("created_at", datetime.now().isoformat())
    (carpeta / nombre).write_text(
        yaml.dump(tarea, allow_unicode=True, default_flow_style=False)
    )
    print(f"  📨 Tarea creada → {destino}/{nombre}")


def guardar_reporte(agente: str, contenido: dict):
    """Guarda un reporte en reports/."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre = f"{ts}_{agente}.json"
    (REPORTS_DIR / nombre).write_text(
        json.dumps(contenido, ensure_ascii=False, indent=2)
    )
    print(f"  📄 Reporte guardado → reports/{nombre}")
    return str(REPORTS_DIR / nombre)


def leer_ultimo_reporte(agente: str) -> Optional[dict]:
    """Lee el ultimo reporte de un agente."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    reportes = sorted(REPORTS_DIR.glob(f"*_{agente}.json"), reverse=True)
    if not reportes:
        return None
    try:
        return json.loads(reportes[0].read_text())
    except Exception:
        return None


def leer_doc(nombre: str) -> str:
    """Lee un documento del repo (docs/, VISION, etc.)."""
    for path in [
        MOTOR_DIR / "docs" / nombre,
        MOTOR_DIR / nombre,
        MOTOR_DIR / "docs" / f"{nombre}.md",
    ]:
        if path.exists():
            return path.read_text()[:8000]
    return f"[Documento {nombre} no encontrado]"
