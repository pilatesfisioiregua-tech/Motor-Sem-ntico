"""Meta-Red: carga inteligencias y marco lingüístico en memoria."""
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
