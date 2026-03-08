"""Carga inteligencias.json y expone datos por inteligencia."""
import json
from pathlib import Path


def cargar_inteligencias() -> dict[str, dict]:
    """Devuelve dict indexado por id con datos de cada inteligencia."""
    path = Path(__file__).parent.parent / "meta_red" / "inteligencias.json"
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    resultado: dict[str, dict] = {}
    for intel_id, data in raw.items():
        meta = data.get("meta_red", {})
        # Extraer objetos exclusivos de las preguntas de extraer
        objetos = []
        if "extraer" in meta:
            objetos = meta["extraer"].get("preguntas", [])

        resultado[intel_id] = {
            "id": data["id"],
            "nombre": data["nombre"],
            "firma": data["firma"],
            "punto_ciego": data["punto_ciego"],
            "categoria": data.get("categoria", ""),
            "objetos_exclusivos": objetos,
        }

    return resultado
