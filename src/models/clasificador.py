"""C2: Single-label classifier — RandomForest sobre B2 (540 peticiones)."""
import pickle
import re
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from src.reactor.config import INTELIGENCIAS_IDS

OUTPUT_PATH = Path(__file__).parent.parent.parent / "models" / "clasificador.pkl"


def _extract_features(textos: list[str]) -> np.ndarray:
    """Extrae 3 features binarias: tiene_numeros, tiene_pregunta, longitud_alta."""
    features = []
    for t in textos:
        tiene_numeros = 1.0 if re.search(r'\d', t) else 0.0
        tiene_pregunta = 1.0 if '?' in t else 0.0
        longitud_alta = 1.0 if len(t) > 100 else 0.0
        features.append([tiene_numeros, tiene_pregunta, longitud_alta])
    return np.array(features)


def train(b2_data: list[dict]) -> dict:
    """Entrena clasificador single-label sobre B2. Devuelve métricas."""
    textos = [item.get("texto", "") for item in b2_data]
    labels = [item.get("inteligencia_primaria", "") for item in b2_data]

    # Filtrar items sin datos válidos
    valid = [(t, l) for t, l in zip(textos, labels) if t and l]
    if not valid:
        return {"modelo": "C2_clasificador", "error": "Sin datos válidos", "cumple": False}

    textos, labels = zip(*valid)
    textos = list(textos)
    labels = list(labels)

    # TF-IDF
    vectorizer = TfidfVectorizer(max_features=500, ngram_range=(1, 2), sublinear_tf=True)
    tfidf_matrix = vectorizer.fit_transform(textos)

    # Features binarias
    bin_features = _extract_features(textos)

    # Combinar TF-IDF + binarias
    X = np.hstack([tfidf_matrix.toarray(), bin_features])

    # Label encoding
    le = LabelEncoder()
    le.fit(INTELIGENCIAS_IDS)
    y = le.transform(labels)

    # Split 80/20
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Entrenar
    clf = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
    clf.fit(X_train, y_train)

    # Evaluar
    y_pred = clf.predict(X_test)
    f1_macro = float(f1_score(y_test, y_pred, average="macro", zero_division=0))
    f1_micro = float(f1_score(y_test, y_pred, average="micro", zero_division=0))

    # Guardar
    model_data = {
        "clf": clf,
        "vectorizer": vectorizer,
        "le": le,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "wb") as f:
        pickle.dump(model_data, f)

    return {
        "modelo": "C2_clasificador",
        "archivo": str(OUTPUT_PATH),
        "f1_macro": round(f1_macro, 4),
        "f1_micro": round(f1_micro, 4),
        "criterio": "f1_macro > 0.75",
        "cumple": bool(f1_macro > 0.75),
        "n_train": len(X_train),
        "n_test": len(X_test),
        "n_clases": len(le.classes_),
    }


def predict(texto: str, top_k: int = 5) -> list[str]:
    """Predice top-k inteligencias para un texto."""
    if not OUTPUT_PATH.exists():
        raise FileNotFoundError(f"Modelo no entrenado: {OUTPUT_PATH}")

    with open(OUTPUT_PATH, "rb") as f:
        model_data = pickle.load(f)

    clf = model_data["clf"]
    vectorizer = model_data["vectorizer"]
    le = model_data["le"]

    tfidf = vectorizer.transform([texto])
    bin_feats = _extract_features([texto])
    X = np.hstack([tfidf.toarray(), bin_feats])

    probas = clf.predict_proba(X)[0]
    top_idx = np.argsort(probas)[::-1][:top_k]
    return [le.classes_[i] for i in top_idx]
