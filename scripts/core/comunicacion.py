"""Sistema de Comunicación Inter-Agente via Estigmergia.

Los agentes NO se hablan directamente.
Dejan "marcas" en un tablón compartido que otros detectan y reaccionan.

Tablón: archivo JSON compartido en memoria/_tablon.json
Cada marca tiene: emisor, tipo, contenido, timestamp, leida_por[]
"""
from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

MEMORIA_DIR = Path(__file__).parent.parent.parent / "memoria"
TABLON_PATH = MEMORIA_DIR / "_tablon.json"


def _cargar_tablon() -> list[dict]:
    MEMORIA_DIR.mkdir(parents=True, exist_ok=True)
    if TABLON_PATH.exists():
        try:
            return json.loads(TABLON_PATH.read_text())
        except Exception:
            return []
    return []


def _guardar_tablon(marcas: list[dict]):
    # Limitar a últimas 200 marcas
    TABLON_PATH.write_text(
        json.dumps(marcas[-200:], ensure_ascii=False, indent=2, default=str)
    )


def dejar_marca(emisor: str, tipo: str, contenido: dict, prioridad: int = 5,
                destino: str = None):
    """Un agente deja una marca en el tablón.

    Args:
        emisor: nombre del agente que deja la marca
        tipo: hallazgo | orden | resultado | pregunta | alerta | aprendizaje | solicitud
        contenido: datos de la marca
        prioridad: 1=urgente, 10=informativo
        destino: agente específico (None = broadcast a todos)
    """
    marcas = _cargar_tablon()
    marcas.append({
        "id": f"{emisor}_{int(time.time() * 1000)}",
        "emisor": emisor,
        "tipo": tipo,
        "contenido": contenido,
        "prioridad": prioridad,
        "destino": destino,
        "timestamp": datetime.now().isoformat(),
        "leida_por": [],
    })
    _guardar_tablon(marcas)


def leer_marcas(lector: str, tipo: str = None, solo_nuevas: bool = True,
                destino_mio: bool = True) -> list[dict]:
    """Un agente lee marcas del tablón.

    Args:
        lector: nombre del agente que lee
        tipo: filtrar por tipo (None = todas)
        solo_nuevas: solo marcas no leídas por este agente
        destino_mio: incluir solo broadcast + dirigidas a mí
    """
    marcas = _cargar_tablon()
    resultado = []

    for m in marcas:
        # Filtrar por tipo
        if tipo and m.get("tipo") != tipo:
            continue

        # Filtrar por destino
        if destino_mio and m.get("destino") and m["destino"] != lector:
            continue

        # Filtrar por nuevas
        if solo_nuevas and lector in m.get("leida_por", []):
            continue

        # No leer mis propias marcas
        if m.get("emisor") == lector:
            continue

        resultado.append(m)

    # Ordenar por prioridad (1=primero)
    resultado.sort(key=lambda m: m.get("prioridad", 5))
    return resultado


def marcar_como_leida(lector: str, marca_id: str):
    """Marca una marca como leída por el agente."""
    marcas = _cargar_tablon()
    for m in marcas:
        if m.get("id") == marca_id:
            if lector not in m.get("leida_por", []):
                m.setdefault("leida_por", []).append(lector)
            break
    _guardar_tablon(marcas)


def marcas_pendientes(lector: str) -> int:
    """Cuántas marcas nuevas tiene un agente."""
    return len(leer_marcas(lector, solo_nuevas=True))


def limpiar_tablon(max_edad_horas: int = 24):
    """Limpia marcas viejas."""
    marcas = _cargar_tablon()
    ahora = time.time()
    frescas = []
    for m in marcas:
        try:
            ts = datetime.fromisoformat(m["timestamp"]).timestamp()
            if ahora - ts < max_edad_horas * 3600:
                frescas.append(m)
        except Exception:
            frescas.append(m)
    _guardar_tablon(frescas)
