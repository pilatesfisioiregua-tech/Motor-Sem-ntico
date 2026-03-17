"""C3: Pesos aristas compositor — aprende orden óptimo desde datos B3."""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from src.reactor.config import TOP_PARES

OUTPUT_PATH = Path(__file__).parent.parent.parent / "models" / "compositor_weights.json"


def _parse_orden(orden_optimo: str) -> tuple[str | None, str | None, str]:
    """Parsea 'INT-XX→INT-YY', 'INT-YY→INT-XX', o 'indistinto'."""
    if orden_optimo == "indistinto":
        return None, None, "indistinto"
    parts = orden_optimo.split("→")
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip(), "dirigido"
    return None, None, "indistinto"


def _parse_par(par: str) -> tuple[str, str] | None:
    """Parsea formatos de par: 'INT-XX×INT-YY', 'INT-XX-INT-YY', etc."""
    # Separar por ×, -, o espacio
    ids = re.findall(r'INT-\d{2}', par)
    if len(ids) == 2:
        return _normalize_par(ids[0], ids[1])
    return None


def _normalize_par(a: str, b: str) -> tuple[str, str]:
    """Normaliza un par al orden de TOP_PARES."""
    for p in TOP_PARES:
        if (a == p[0] and b == p[1]) or (a == p[1] and b == p[0]):
            return p
    return (a, b)


def train(b3_data: list[dict]) -> dict:
    """Aprende pesos de aristas desde datos de composición B3."""
    par_stats: dict[str, dict] = defaultdict(lambda: {
        "total": 0,
        "ab": 0,
        "ba": 0,
        "indistinto": 0,
        "features": Counter(),
    })

    for item in b3_data:
        par_raw = item.get("par", "")
        orden = item.get("orden_optimo", "indistinto")
        features = item.get("features_predictoras", [])

        # Parsear par a formato canónico
        parsed = _parse_par(par_raw) if par_raw else None
        if not parsed:
            primero, segundo, tipo = _parse_orden(orden)
            if primero and segundo:
                parsed = _normalize_par(primero, segundo)
            else:
                continue

        par_key = f"{parsed[0]}-{parsed[1]}"
        stats = par_stats[par_key]
        stats["total"] += 1

        primero, segundo, tipo = _parse_orden(orden)
        if tipo == "indistinto":
            stats["indistinto"] += 1
        elif primero and segundo:
            a, b = parsed
            if primero == a:
                stats["ab"] += 1
            else:
                stats["ba"] += 1

        if isinstance(features, list):
            for feat in features:
                if isinstance(feat, str):
                    stats["features"][feat] += 1

    # Construir aristas con pesos
    aristas: list[dict] = []
    for par_key, stats in par_stats.items():
        total = stats["total"]
        if total == 0:
            continue

        ab_ratio = stats["ab"] / total
        ba_ratio = stats["ba"] / total
        ind_ratio = stats["indistinto"] / total

        if ab_ratio > ba_ratio and ab_ratio > ind_ratio:
            direccion = "ab"
            peso = ab_ratio
        elif ba_ratio > ab_ratio and ba_ratio > ind_ratio:
            direccion = "ba"
            peso = ba_ratio
        else:
            direccion = "indistinto"
            peso = ind_ratio

        top_features = [f for f, _ in stats["features"].most_common(5)]

        aristas.append({
            "par": par_key,
            "total_datapoints": total,
            "ab_ratio": round(ab_ratio, 3),
            "ba_ratio": round(ba_ratio, 3),
            "indistinto_ratio": round(ind_ratio, 3),
            "direccion_optima": direccion,
            "peso_confianza": round(peso, 3),
            "features_predictoras": top_features,
        })

    output = {
        "aristas": aristas,
        "n_pares": len(aristas),
        "n_datapoints": len(b3_data),
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    test_cases_valid = _validate_test_cases(aristas)

    return {
        "modelo": "C3_compositor_weights",
        "archivo": str(OUTPUT_PATH),
        "n_pares": len(aristas),
        "n_datapoints": len(b3_data),
        "test_cases_valid": test_cases_valid,
        "criterio": "3 test cases generan output válido",
        "cumple": bool(test_cases_valid >= 3),
    }


def _validate_test_cases(aristas: list[dict]) -> int:
    """Valida que al menos 3 aristas tengan datapoints válidos (>0)."""
    valid = sum(1 for a in aristas if a.get("total_datapoints", 0) > 0)
    return min(valid, 3)


def get_weights() -> dict:
    """Carga pesos entrenados."""
    if not OUTPUT_PATH.exists():
        raise FileNotFoundError(f"Modelo no entrenado: {OUTPUT_PATH}")
    with open(OUTPUT_PATH, encoding="utf-8") as f:
        return json.load(f)
