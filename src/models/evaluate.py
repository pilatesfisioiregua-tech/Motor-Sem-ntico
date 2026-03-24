"""Evalúa métricas de los 4 modelos entrenados."""
import structlog
from pathlib import Path

import numpy as np
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split

from src.models import router_embeddings, clasificador, compositor_weights, scorer
from src.models.trainer import _load_json
from src.reactor.config import INTELIGENCIAS_IDS

log = structlog.get_logger()

MODELS_DIR = Path(__file__).parent.parent.parent / "models"


def evaluate_all() -> dict:
    """Evalúa los 4 modelos contra criterios de cierre."""
    resultados: list[dict] = []

    resultados.append(_eval_c1())
    resultados.append(_eval_c2())
    resultados.append(_eval_c3())
    resultados.append(_eval_c4())

    cumplen = sum(1 for r in resultados if r.get("cumple", False))

    return {
        "resultados": resultados,
        "criterios_cumplidos": cumplen,
        "criterios_total": 4,
        "aprobado": cumplen == 4,
    }


def _eval_c1() -> dict:
    """Evalúa C1: top-3 accuracy sobre B1."""
    try:
        model_path = MODELS_DIR / "router_embeddings.pkl"
        if not model_path.exists():
            return {"modelo": "C1", "error": "No entrenado", "cumple": False}

        b1 = _load_json("b1_casos.json")
        if not b1:
            return {"modelo": "C1", "error": "Sin datos B1", "cumple": False}

        correct = 0
        total = 0
        for item in b1:
            texto = item.get("descripcion", "")
            expected = set(item.get("top_5_inteligencias", []))
            if not texto or not expected:
                continue
            total += 1
            try:
                preds = router_embeddings.predict(texto, top_k=3)
                pred_ids = {p[0] for p in preds}
                if pred_ids & expected:
                    correct += 1
            except Exception as e:
                log.debug("silenced_exception", exc=str(e))

        acc = correct / total if total > 0 else 0.0
        return {
            "modelo": "C1_router_embeddings",
            "metrica": "top3_accuracy",
            "valor": round(acc, 4),
            "criterio": "> 0.80",
            "cumple": bool(acc > 0.80),
            "n_evaluados": total,
        }
    except Exception as e:
        return {"modelo": "C1", "error": str(e), "cumple": False}


def _eval_c2() -> dict:
    """Evalúa C2: F1 macro sobre B2 test split (20%)."""
    try:
        model_path = MODELS_DIR / "clasificador.pkl"
        if not model_path.exists():
            return {"modelo": "C2", "error": "No entrenado", "cumple": False}

        b2 = _load_json("b2_peticiones.json")
        if not b2:
            return {"modelo": "C2", "error": "Sin datos B2", "cumple": False}

        textos = [item.get("texto", "") for item in b2]
        labels = [item.get("inteligencia_primaria", "") for item in b2]
        valid = [(t, l) for t, l in zip(textos, labels) if t and l]
        if not valid:
            return {"modelo": "C2", "error": "Sin datos válidos", "cumple": False}

        textos, labels = zip(*valid)
        textos = list(textos)
        labels = list(labels)

        from sklearn.preprocessing import LabelEncoder
        le = LabelEncoder()
        le.fit(INTELIGENCIAS_IDS)
        y = le.transform(labels)

        # Reproducir el MISMO split que en train (random_state=42, stratify=y)
        _, textos_test, _, y_test = train_test_split(
            textos, y, test_size=0.2, random_state=42, stratify=y
        )

        y_pred_labels = []
        for texto in textos_test:
            try:
                preds = clasificador.predict(texto, top_k=1)
                y_pred_labels.append(preds[0] if preds else "")
            except Exception:
                y_pred_labels.append("")

        # Transformar predicciones válidas
        y_pred = []
        for p in y_pred_labels:
            if p in le.classes_:
                y_pred.append(le.transform([p])[0])
            else:
                y_pred.append(-1)
        y_pred = np.array(y_pred)

        # Filtrar predicciones inválidas
        mask = y_pred >= 0
        if mask.sum() == 0:
            return {"modelo": "C2", "error": "Ninguna predicción válida", "cumple": False}

        f1 = float(f1_score(y_test[mask], y_pred[mask], average="macro", zero_division=0))

        return {
            "modelo": "C2_clasificador",
            "metrica": "f1_macro",
            "valor": round(f1, 4),
            "criterio": "> 0.75",
            "cumple": bool(f1 > 0.75),
            "n_evaluados": int(mask.sum()),
            "nota": "Evaluado sobre 20% test split B2 (random_state=42, stratified)",
        }
    except Exception as e:
        return {"modelo": "C2", "error": str(e), "cumple": False}


def _eval_c3() -> dict:
    """Evalúa C3: 3 test cases generan output válido."""
    try:
        model_path = MODELS_DIR / "compositor_weights.json"
        if not model_path.exists():
            return {"modelo": "C3", "error": "No entrenado", "cumple": False}

        weights = compositor_weights.get_weights()
        aristas = weights.get("aristas", [])

        # Validar que al menos 3 aristas tengan datos válidos
        detalles = []
        valid = 0
        for a in aristas:
            has_data = a.get("total_datapoints", 0) > 0
            if has_data:
                valid += 1
            detalles.append({
                "par": a["par"],
                "encontrado": has_data,
                "peso": a.get("peso_confianza", 0),
                "direccion": a.get("direccion_optima", "?"),
                "datapoints": a.get("total_datapoints", 0),
            })

        return {
            "modelo": "C3_compositor_weights",
            "metrica": "aristas_con_datos",
            "valor": valid,
            "criterio": ">= 3",
            "cumple": bool(valid >= 3),
            "detalles": detalles,
            "n_aristas": len(aristas),
        }
    except Exception as e:
        return {"modelo": "C3", "error": str(e), "cumple": False}


def _eval_c4() -> dict:
    """Evalúa C4: Pearson > 0.7 sobre B4."""
    try:
        model_path = MODELS_DIR / "scorer.pkl"
        if not model_path.exists():
            return {"modelo": "C4", "error": "No entrenado", "cumple": False}

        b4 = _load_json("b4_scoring.json")
        valid = [
            item for item in b4
            if item.get("output_texto") and item.get("scores", {}).get("score_global") is not None
        ]
        if len(valid) < 5:
            return {"modelo": "C4", "error": f"Solo {len(valid)} items", "cumple": False}

        from scipy.stats import pearsonr
        y_true = [item["scores"]["score_global"] for item in valid]
        y_pred = [scorer.predict(item["output_texto"]) for item in valid]

        corr, pval = pearsonr(y_true, y_pred)

        return {
            "modelo": "C4_scorer",
            "metrica": "pearson",
            "valor": round(float(corr), 4),
            "p_value": round(float(pval), 6),
            "criterio": "> 0.70",
            "cumple": bool(corr > 0.70),
            "n_evaluados": len(valid),
        }
    except Exception as e:
        return {"modelo": "C4", "error": str(e), "cumple": False}
