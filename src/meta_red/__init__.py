"""Meta-Red: carga inteligencias y marco lingüístico en memoria."""
from __future__ import annotations

import json
from pathlib import Path

_BASE = Path(__file__).parent

_inteligencias: dict | None = None
_marco: dict | None = None


def load_inteligencias() -> dict:
    """Carga inteligencias.json en memoria (singleton)."""
    global _inteligencias
    if _inteligencias is None:
        _inteligencias = json.loads((_BASE / "inteligencias.json").read_text())
    return _inteligencias


def load_marco_linguistico() -> dict:
    """Carga marco_linguistico.json en memoria (singleton)."""
    global _marco
    if _marco is None:
        _marco = json.loads((_BASE / "marco_linguistico.json").read_text())
    return _marco


_razonamientos: dict | None = None


def load_razonamientos() -> dict:
    """Carga razonamientos.json en memoria (singleton)."""
    global _razonamientos
    if _razonamientos is None:
        _razonamientos = json.loads((_BASE / "razonamientos.json").read_text())
    return _razonamientos


_pensamientos: dict | None = None


def load_pensamientos() -> dict:
    """Carga pensamientos.json en memoria (singleton)."""
    global _pensamientos
    if _pensamientos is None:
        _pensamientos = json.loads((_BASE / "pensamientos.json").read_text())
    return _pensamientos
