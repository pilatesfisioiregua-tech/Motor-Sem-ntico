"""C4: Ridge scorer — predice score_global desde features del output."""
import pickle
import re
from pathlib import Path

import numpy as np
from scipy.stats import pearsonr
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split

OUTPUT_PATH = Path(__file__).parent.parent.parent / "models" / "scorer.pkl"


def _extract_features(outputs: list[dict]) -> np.ndarray:
    """Extrae 9 features numéricas de cada output."""
    features = []
    for item in outputs:
        texto = item.get("output_texto", "")
        palabras = texto.split()
        n_palabras = len(palabras)

        longitud = len(texto)
        num_hallazgos = len(re.findall(
            r'hallazgo|descubrimiento|insight|patrón|clave|revela|evidencia|diagnóstico',
            texto, re.IGNORECASE
        ))
        tiene_numeros = 1.0 if re.search(r'\d+[%€$]|\d+\.\d+|\d{2,}', texto) else 0.0
        tiene_preguntas = 1.0 if '?' in texto else 0.0
        tiene_frontera = 1.0 if re.search(
            r'frontera|límite|tensión|paradoja|dilema|punto ciego|asume|no examina',
            texto, re.IGNORECASE
        ) else 0.0
        diversidad_vocab = len(set(palabras)) / max(n_palabras, 1)

        n_parrafos = max(texto.count('\n\n'), 1)
        densidad_datos = len(re.findall(r'\d+', texto)) / max(n_palabras, 1)
        tiene_estructura = 1.0 if re.search(
            r'EXTRAER|CRUZAR|INTEGRAR|ABSTRAER|FRONTERA|L[1-6]|Paso \d|##|###',
            texto
        ) else 0.0

        features.append([
            longitud,
            num_hallazgos,
            tiene_numeros,
            tiene_preguntas,
            tiene_frontera,
            diversidad_vocab,
            n_parrafos,
            densidad_datos,
            tiene_estructura,
        ])
    return np.array(features)


def train(b4_data: list[dict]) -> dict:
    """Entrena Ridge scorer. Devuelve métricas."""
    # Filtrar items válidos
    valid = [
        item for item in b4_data
        if item.get("output_texto") and item.get("scores", {}).get("score_global") is not None
    ]
    if len(valid) < 10:
        return {"modelo": "C4_scorer", "error": f"Solo {len(valid)} items válidos", "cumple": False}

    X = _extract_features(valid)
    y = np.array([item["scores"]["score_global"] for item in valid])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Ridge primario
    ridge = Ridge(alpha=1.0)
    ridge.fit(X_train, y_train)
    y_pred_ridge = ridge.predict(X_test)

    if len(y_test) > 2:
        corr_ridge, _ = pearsonr(y_test, y_pred_ridge)
    else:
        corr_ridge = 0.0

    # Fallback: RandomForest si Ridge no cumple
    rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    y_pred_rf = rf.predict(X_test)

    if len(y_test) > 2:
        corr_rf, _ = pearsonr(y_test, y_pred_rf)
    else:
        corr_rf = 0.0

    # Elegir mejor modelo
    if corr_ridge >= corr_rf:
        best_model = ridge
        best_corr = corr_ridge
        model_type = "Ridge"
    else:
        best_model = rf
        best_corr = corr_rf
        model_type = "RandomForest"

    model_data = {
        "model": best_model,
        "model_type": model_type,
        "feature_names": [
            "longitud", "num_hallazgos", "tiene_numeros",
            "tiene_preguntas", "tiene_frontera", "diversidad_vocab",
            "n_parrafos", "densidad_datos", "tiene_estructura",
        ],
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "wb") as f:
        pickle.dump(model_data, f)

    return {
        "modelo": "C4_scorer",
        "archivo": str(OUTPUT_PATH),
        "model_type": model_type,
        "pearson_ridge": round(float(corr_ridge), 4),
        "pearson_rf": round(float(corr_rf), 4),
        "pearson_best": round(float(best_corr), 4),
        "criterio": "pearson > 0.70",
        "cumple": bool(best_corr > 0.70),
        "n_train": len(X_train),
        "n_test": len(X_test),
    }


def predict(output_texto: str) -> float:
    """Predice score_global para un texto de output."""
    if not OUTPUT_PATH.exists():
        raise FileNotFoundError(f"Modelo no entrenado: {OUTPUT_PATH}")

    with open(OUTPUT_PATH, "rb") as f:
        model_data = pickle.load(f)

    item = {"output_texto": output_texto}
    X = _extract_features([item])
    score = float(model_data["model"].predict(X)[0])
    return max(0.0, min(1.0, score))
