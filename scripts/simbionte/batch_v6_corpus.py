"""
Batch v6 — Procesar corpus completo con Simbionte v6 (361D) + geometria
Fecha: 2026-04-12

Procesa N textos del gold_set_v2 y produce:
  - Vector 361D por texto (266D marcos + 95D geometria)
  - Clusters de formas geometricas
  - Estadisticas de isomorfismos emergentes

$0 total — todo determinista (spaCy + NumPy + SciPy + NetworkX)
"""

import json
import time
import sys
import os
import numpy as np
from collections import Counter

sys.path.insert(0, os.path.dirname(__file__))

import spacy

from poc_capa0_v6 import calcular_vector_v6
from marcos_matematicos import FEATURES_POR_NIVEL
from geometria_isomorfismo import calcular_geometria_completa, FEATURES_GEOMETRIA_TOTAL


def process_batch(input_path, output_path, max_texts=None, report_every=50):
    """Procesa batch de textos con Simbionte v6."""

    lang = os.environ.get("SIMBIONTE_LANG", "es")
    model_name = "en_core_web_trf" if lang == "en" else "es_dep_news_trf"
    print(f"Cargando spaCy {model_name} (lang={lang})...")
    nlp = spacy.load(model_name)
    FPN = FEATURES_POR_NIVEL

    # Leer textos
    texts = []
    with open(input_path) as f:
        for line in f:
            d = json.loads(line.strip())
            texts.append({"id": d.get("custom_id", f"t_{len(texts)}"), "text": d["text"]})
            if max_texts and len(texts) >= max_texts:
                break

    print(f"Textos cargados: {len(texts)}")
    print(f"Procesando con Simbionte v6 (361D)...\n")

    results = []
    vectors_geo = []  # Para clustering
    tiempos = []
    errores = []
    t_total = time.time()

    for i, item in enumerate(texts):
        t0 = time.time()
        try:
            doc = nlp(item["text"][:5000])  # Cap a 5000 chars para evitar textos gigantes

            # Vector v6 (266D)
            vector_v6, meta = calcular_vector_v6(doc)

            # Geometria (95D)
            vectores_nivel = {
                "N1": vector_v6[0:FPN],
                "N2": vector_v6[FPN:2*FPN],
                "N3": vector_v6[2*FPN:3*FPN],
                "N4": vector_v6[3*FPN:4*FPN],
            }
            geo = calcular_geometria_completa(vectores_nivel)

            # Vector completo
            vector_total = np.concatenate([vector_v6, geo["vector_pgvector"]])

            dt = time.time() - t0
            tiempos.append(dt)

            # Extraer metricas clave
            dominantes = {}
            for nivel in ["N1", "N2", "N3", "N4"]:
                dom = geo["geometrias"][nivel]["forma"]["dominantes"]
                if dom:
                    dominantes[nivel] = dom

            results.append({
                "id": item["id"],
                "n_tokens": meta["n_tokens"],
                "n_oraciones": meta["n_oraciones"],
                "profundidad": geo["profundidad_patron"],
                "dominantes": dominantes,
                "simetria_N2": geo["geometrias"]["N2"]["forma"]["simetria"],
                "coherencia_N2": geo["geometrias"]["N2"]["forma"]["coherencia"],
                "latencia_ms": round(dt * 1000),
            })
            vectors_geo.append(geo["vector_pgvector"])

        except Exception as e:
            errores.append({"id": item["id"], "error": str(e)})
            dt = time.time() - t0
            tiempos.append(dt)

        if (i + 1) % report_every == 0:
            elapsed = time.time() - t_total
            avg_ms = np.mean(tiempos[-report_every:]) * 1000
            eta = (len(texts) - i - 1) * np.mean(tiempos)
            print(f"  [{i+1}/{len(texts)}] avg={avg_ms:.0f}ms/texto, elapsed={elapsed:.0f}s, ETA={eta:.0f}s, errors={len(errores)}")

    dt_total = time.time() - t_total

    # Estadisticas
    print(f"\n{'='*60}")
    print(f"BATCH COMPLETADO")
    print(f"{'='*60}")
    print(f"  Textos procesados: {len(results)}/{len(texts)}")
    print(f"  Errores: {len(errores)}")
    print(f"  Tiempo total: {dt_total:.1f}s ({dt_total/60:.1f}min)")
    print(f"  Media: {np.mean(tiempos)*1000:.0f}ms/texto")
    print(f"  P50: {np.percentile(tiempos, 50)*1000:.0f}ms | P95: {np.percentile(tiempos, 95)*1000:.0f}ms | P99: {np.percentile(tiempos, 99)*1000:.0f}ms")

    # Clustering de geometrias
    if vectors_geo:
        X = np.array(vectors_geo)
        print(f"\n  GEOMETRIAS:")
        print(f"  Shape: {X.shape}")
        print(f"  NaN: {np.isnan(X).sum()}, Inf: {np.isinf(X).sum()}")
        print(f"  Non-zero: {(X!=0).sum()}/{X.size} ({(X!=0).sum()/X.size*100:.1f}%)")

        # Clustering simple: k-means sobre geometria
        from sklearn.cluster import KMeans
        from sklearn.metrics import silhouette_score

        # Normalizar
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        X_norm = scaler.fit_transform(X)
        X_norm = np.nan_to_num(X_norm, 0)

        # Probar k=3..10
        print(f"\n  CLUSTERING (k-means sobre geometria 95D):")
        best_k, best_sil = 3, -1
        for k in range(3, min(11, len(results))):
            km = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = km.fit_predict(X_norm)
            sil = silhouette_score(X_norm, labels)
            print(f"    k={k}: silhouette={sil:.3f}")
            if sil > best_sil:
                best_sil = sil
                best_k = k

        print(f"  Mejor k={best_k} (silhouette={best_sil:.3f})")

        # Asignar clusters
        km_best = KMeans(n_clusters=best_k, random_state=42, n_init=10)
        labels = km_best.fit_predict(X_norm)

        # Profundidad por cluster
        print(f"\n  CLUSTERS:")
        for c in range(best_k):
            mask = labels == c
            n_c = mask.sum()
            profs = [results[i]["profundidad"] for i in range(len(results)) if mask[i]]
            prof_mean = np.mean(profs)

            # Dominantes mas frecuentes en este cluster
            all_dom = []
            for i in range(len(results)):
                if mask[i]:
                    for nivel, doms in results[i]["dominantes"].items():
                        all_dom.extend(doms)
            dom_freq = Counter(all_dom).most_common(3)
            dom_str = ", ".join(f"{d}({c})" for d, c in dom_freq)

            print(f"    Cluster {c}: n={n_c} ({n_c/len(results)*100:.1f}%), prof_media={prof_mean:.3f}, dominantes=[{dom_str}]")

        # Guardar
        for i, r in enumerate(results):
            r["cluster"] = int(labels[i])

    # Guardar resultados
    save = {
        "version": "batch_v6",
        "fecha": time.strftime("%Y-%m-%d %H:%M"),
        "n_textos": len(results),
        "n_errores": len(errores),
        "tiempo_total_s": round(dt_total, 1),
        "media_ms": round(np.mean(tiempos) * 1000),
        "p95_ms": round(np.percentile(tiempos, 95) * 1000),
        "best_k": best_k if vectors_geo else None,
        "best_silhouette": round(best_sil, 4) if vectors_geo else None,
        "results": results[:100],  # Solo primeros 100 para no hacer archivo enorme
        "errores": errores[:20],
    }

    with open(output_path, "w") as f:
        json.dump(save, f, ensure_ascii=False, indent=2)
    print(f"\nGuardado en {output_path}")

    # Guardar vectores para pgvector
    if vectors_geo:
        vectors_path = output_path.replace(".json", "_vectors.npy")
        np.save(vectors_path, np.array(vectors_geo))
        print(f"Vectores geometria: {vectors_path} ({np.array(vectors_geo).shape})")

    return results, vectors_geo


if __name__ == "__main__":
    input_path = os.path.join(os.path.dirname(__file__), "../../data/gold_set_v2_3000.texts.jsonl")
    output_path = os.path.join(os.path.dirname(__file__), "../../data/batch_v6_corpus.json")

    max_texts = int(sys.argv[1]) if len(sys.argv) > 1 else 50  # Default: 50 (T1 empezar pequeño)

    process_batch(input_path, output_path, max_texts=max_texts)
