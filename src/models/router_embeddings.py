"""C1: TF-IDF router — proxy de embeddings sin Voyage/sentence-transformers."""
import pickle
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.reactor.config import INTELIGENCIAS_IDS
from src.reactor.cartografia_loader import cargar_inteligencias

OUTPUT_PATH = Path(__file__).parent.parent.parent / "models" / "router_embeddings.pkl"


def _build_reference_texts(inteligencias: dict[str, dict]) -> dict[str, str]:
    """Construye texto de referencia por inteligencia: firma + punto_ciego + objetos."""
    refs: dict[str, str] = {}
    for intel_id in INTELIGENCIAS_IDS:
        data = inteligencias.get(intel_id, {})
        parts = [
            data.get("firma", ""),
            data.get("punto_ciego", ""),
        ]
        objetos = data.get("objetos_exclusivos", [])
        if isinstance(objetos, list):
            parts.extend(objetos)
        refs[intel_id] = " ".join(parts)
    return refs


def train(b1_data: list[dict], b2_data: list[dict]) -> dict:
    """Entrena TF-IDF router. Devuelve métricas."""
    import json as _json
    inteligencias = cargar_inteligencias()

    # Texto rico: meta_red completa (nombre, preguntas, lentes, etc.)
    raw_path = Path(__file__).parent.parent / "meta_red" / "inteligencias.json"
    with open(raw_path, encoding="utf-8") as f:
        inteligencias_raw = _json.load(f)
    ref_texts = _build_rich_reference_texts(inteligencias_raw)

    ref_ids = list(ref_texts.keys())
    ref_corpus = [ref_texts[k] for k in ref_ids]

    b2_texts = [item.get("texto", "") for item in b2_data]
    b2_labels = [item.get("inteligencia_primaria", "") for item in b2_data]

    full_corpus = ref_corpus + b2_texts

    vectorizer = TfidfVectorizer(
        max_features=1000,
        ngram_range=(1, 2),
        sublinear_tf=True,
        min_df=1,
    )
    tfidf_matrix = vectorizer.fit_transform(full_corpus)

    ref_vectors_raw = tfidf_matrix[:len(ref_ids)]
    b2_vectors = tfidf_matrix[len(ref_ids):]

    # Centroides B2 puros (alpha=0): usar centroide B2 como referencia
    # Fallback a cartografía solo si una inteligencia no tiene textos en B2
    ref_arrays = ref_vectors_raw.toarray()
    b2_by_intel: dict[str, list[int]] = {iid: [] for iid in ref_ids}
    for i, label in enumerate(b2_labels):
        if label in b2_by_intel:
            b2_by_intel[label].append(i)

    for idx, intel_id in enumerate(ref_ids):
        indices = b2_by_intel[intel_id]
        if indices:
            ref_arrays[idx] = b2_vectors[indices].toarray().mean(axis=0)

    from scipy.sparse import csr_matrix
    ref_vectors = csr_matrix(ref_arrays)

    # Cosine similarity de cada texto B2 contra las 18 referencias enriquecidas
    sim_matrix = cosine_similarity(b2_vectors, ref_vectors)

    # Grid search de threshold sobre B2 (top-1 accuracy)
    best_threshold = 0.0
    best_acc = 0.0

    for threshold in np.arange(0.0, 0.5, 0.01):
        correct = 0
        total = 0
        for i, label in enumerate(b2_labels):
            if label not in ref_ids:
                continue
            total += 1
            top_idx = np.argsort(sim_matrix[i])[::-1][0]
            if sim_matrix[i][top_idx] >= threshold and ref_ids[top_idx] == label:
                correct += 1
        if total > 0:
            acc = correct / total
            if acc > best_acc:
                best_acc = acc
                best_threshold = float(threshold)

    # Top-3 accuracy sobre B1 (top_5_inteligencias)
    b1_texts = [item.get("descripcion", "") for item in b1_data]
    b1_labels = [item.get("top_5_inteligencias", []) for item in b1_data]

    if b1_texts:
        b1_vectors = vectorizer.transform(b1_texts)
        b1_sim = cosine_similarity(b1_vectors, ref_vectors)

        top3_correct = 0
        top3_total = 0
        for i, labels in enumerate(b1_labels):
            if not labels:
                continue
            top3_total += 1
            top3_idx = np.argsort(b1_sim[i])[::-1][:3]
            top3_preds = {ref_ids[j] for j in top3_idx}
            if top3_preds & set(labels):
                top3_correct += 1
        top3_acc = top3_correct / top3_total if top3_total > 0 else 0.0
    else:
        top3_acc = 0.0

    # Serializar con pickle (vectorizer fitted completo)
    ref_vectors_dict = {
        ref_ids[i]: ref_vectors[i].toarray()[0].tolist()
        for i in range(len(ref_ids))
    }

    output = {
        "vectorizer": vectorizer,
        "ref_vectors": ref_vectors_dict,
        "threshold": best_threshold,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "wb") as f:
        pickle.dump(output, f)

    return {
        "modelo": "C1_router_embeddings",
        "archivo": str(OUTPUT_PATH),
        "threshold": best_threshold,
        "top1_accuracy_b2": best_acc,
        "top3_accuracy_b1": top3_acc,
        "criterio": "top3_accuracy > 0.80",
        "cumple": bool(top3_acc > 0.80),
        "n_b1": len(b1_data),
        "n_b2": len(b2_data),
    }


def _build_rich_reference_texts(inteligencias_raw: dict) -> dict[str, str]:
    """Construye texto de referencia enriquecido con meta_red completa."""
    refs: dict[str, str] = {}
    for intel_id in INTELIGENCIAS_IDS:
        data = inteligencias_raw.get(intel_id, {})
        parts = [
            data.get("nombre", ""),
            data.get("firma", ""),
            data.get("punto_ciego", ""),
            data.get("categoria", ""),
        ]
        mr = data.get("meta_red", {})
        # Extraer preguntas de cada sección
        for section in ["extraer", "cruzar"]:
            sec = mr.get(section, {})
            if isinstance(sec, dict):
                parts.append(sec.get("nombre", ""))
                parts.extend(sec.get("preguntas", []))
        # Lentes
        for lens in mr.get("lentes", []):
            parts.append(lens.get("nombre", ""))
            parts.extend(lens.get("preguntas", []))
        # Strings directos
        for section in ["integrar", "abstraer", "frontera"]:
            val = mr.get(section, "")
            if isinstance(val, str):
                parts.append(val)
        refs[intel_id] = " ".join(p for p in parts if p)
    return refs


def explore(b1_data: list[dict], b2_data: list[dict]) -> list[dict]:
    """Prueba múltiples configuraciones de C1 y reporta top-3 accuracy de cada una."""
    import json
    from pathlib import Path

    inteligencias = cargar_inteligencias()

    # Cargar inteligencias.json raw para textos ricos
    raw_path = Path(__file__).parent.parent / "meta_red" / "inteligencias.json"
    with open(raw_path, encoding="utf-8") as f:
        inteligencias_raw = json.load(f)

    ref_texts_basic = _build_reference_texts(inteligencias)
    ref_texts_rich = _build_rich_reference_texts(inteligencias_raw)

    b2_texts = [item.get("texto", "") for item in b2_data]
    b2_labels = [item.get("inteligencia_primaria", "") for item in b2_data]
    b1_texts = [item.get("descripcion", "") for item in b1_data]
    b1_labels = [item.get("top_5_inteligencias", []) for item in b1_data]

    configs = [
        # (name, ref_texts, max_features, ngram, alpha)
        ("baseline_basic_a50", ref_texts_basic, 1000, (1, 2), 0.5),
        ("basic_a30", ref_texts_basic, 1000, (1, 2), 0.3),
        ("basic_a20", ref_texts_basic, 1000, (1, 2), 0.2),
        ("basic_a70", ref_texts_basic, 1000, (1, 2), 0.7),
        ("basic_a00_pure_centroid", ref_texts_basic, 1000, (1, 2), 0.0),
        ("rich_a50", ref_texts_rich, 1000, (1, 2), 0.5),
        ("rich_a30", ref_texts_rich, 1000, (1, 2), 0.3),
        ("rich_a20", ref_texts_rich, 1000, (1, 2), 0.2),
        ("rich_a00", ref_texts_rich, 1000, (1, 2), 0.0),
        ("rich_2k_a30", ref_texts_rich, 2000, (1, 2), 0.3),
        ("rich_2k_a20", ref_texts_rich, 2000, (1, 2), 0.2),
        ("rich_3gram_a30", ref_texts_rich, 1000, (1, 3), 0.3),
        ("rich_2k_3gram_a20", ref_texts_rich, 2000, (1, 3), 0.2),
        ("rich_2k_3gram_a30", ref_texts_rich, 2000, (1, 3), 0.3),
        ("basic_2k_a30", ref_texts_basic, 2000, (1, 2), 0.3),
        ("basic_3gram_a30", ref_texts_basic, 1000, (1, 3), 0.3),
    ]

    results = []
    for name, ref_txts, max_feat, ngram, alpha in configs:
        try:
            acc = _eval_config(
                ref_txts, b2_texts, b2_labels, b1_texts, b1_labels,
                max_feat, ngram, alpha
            )
            results.append({
                "config": name,
                "top3_accuracy": round(acc, 4),
                "pasa": bool(acc > 0.80),
            })
        except Exception as e:
            results.append({"config": name, "error": str(e)})

    results.sort(key=lambda x: x.get("top3_accuracy", 0), reverse=True)
    return results


def _eval_config(
    ref_texts: dict[str, str],
    b2_texts: list[str],
    b2_labels: list[str],
    b1_texts: list[str],
    b1_labels: list[list[str]],
    max_features: int,
    ngram_range: tuple[int, int],
    alpha: float,
) -> float:
    """Evalúa una configuración. alpha = peso de cartografía (1-alpha = peso centroides B2)."""
    ref_ids = list(ref_texts.keys())
    ref_corpus = [ref_texts[k] for k in ref_ids]

    full_corpus = ref_corpus + b2_texts
    vectorizer = TfidfVectorizer(
        max_features=max_features, ngram_range=ngram_range,
        sublinear_tf=True, min_df=1,
    )
    tfidf_matrix = vectorizer.fit_transform(full_corpus)

    ref_vectors_raw = tfidf_matrix[:len(ref_ids)].toarray()
    b2_vectors = tfidf_matrix[len(ref_ids):]

    # Centroides B2
    b2_by_intel: dict[str, list[int]] = {iid: [] for iid in ref_ids}
    for i, label in enumerate(b2_labels):
        if label in b2_by_intel:
            b2_by_intel[label].append(i)

    ref_arrays = ref_vectors_raw.copy()
    for idx, intel_id in enumerate(ref_ids):
        indices = b2_by_intel[intel_id]
        if indices:
            centroid = b2_vectors[indices].toarray().mean(axis=0)
            ref_arrays[idx] = alpha * ref_arrays[idx] + (1 - alpha) * centroid

    from scipy.sparse import csr_matrix
    ref_vectors = csr_matrix(ref_arrays)

    # Top-3 accuracy sobre B1
    b1_vecs = vectorizer.transform(b1_texts)
    b1_sim = cosine_similarity(b1_vecs, ref_vectors)

    correct = 0
    total = 0
    for i, labels in enumerate(b1_labels):
        if not labels:
            continue
        total += 1
        top3_idx = np.argsort(b1_sim[i])[::-1][:3]
        top3_preds = {ref_ids[j] for j in top3_idx}
        if top3_preds & set(labels):
            correct += 1

    return correct / total if total > 0 else 0.0


def predict(texto: str, top_k: int = 5) -> list[tuple[str, float]]:
    """Predice top-k inteligencias para un texto dado."""
    if not OUTPUT_PATH.exists():
        raise FileNotFoundError(f"Modelo no entrenado: {OUTPUT_PATH}")

    with open(OUTPUT_PATH, "rb") as f:
        model = pickle.load(f)

    vectorizer = model["vectorizer"]
    ref_vectors = model["ref_vectors"]

    text_vector = vectorizer.transform([texto]).toarray()[0]

    scores: list[tuple[str, float]] = []
    for intel_id, ref_vec in ref_vectors.items():
        ref_arr = np.array(ref_vec)
        norm_text = np.linalg.norm(text_vector)
        norm_ref = np.linalg.norm(ref_arr)
        if norm_text == 0 or norm_ref == 0:
            sim = 0.0
        else:
            sim = float(np.dot(text_vector, ref_arr) / (norm_text * norm_ref))
        scores.append((intel_id, sim))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_k]
