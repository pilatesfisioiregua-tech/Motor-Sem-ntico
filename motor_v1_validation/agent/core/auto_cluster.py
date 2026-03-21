"""Auto-clustering — k-means on knowledge_base embeddings.

Discovers knowledge groups that aren't obvious from scope/tipo alone.
Populates knowledge_clusters table. Run periodically (weekly recommended).

Usage:
    from core.auto_cluster import run_clustering
    stats = run_clustering(n_clusters=20)

    # Or from CLI:
    python3 -m core.auto_cluster --n-clusters 20
"""

import os
import json
import time
import logging
import numpy as np
from typing import Optional

logger = logging.getLogger(__name__)


def _get_conn():
    import psycopg2
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        url = "postgres://chief_os_omni:77qJGeKtMTgCYhz@localhost:15432/omni_mind"
    conn = psycopg2.connect(url, connect_timeout=15)
    conn.autocommit = False
    return conn


def _load_embeddings(conn, min_rows: int = 100) -> tuple:
    """Load all embeddings from knowledge_base.

    Returns (ids, vectors_np) where vectors_np is a numpy array.
    """
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, embedding::text
            FROM knowledge_base
            WHERE embedding IS NOT NULL
            ORDER BY id
        """)
        rows = cur.fetchall()

    if len(rows) < min_rows:
        logger.warning(f"Only {len(rows)} embedded rows, need {min_rows}+")
        return [], np.array([])

    ids = [r[0] for r in rows]
    vectors = []
    for r in rows:
        # Parse vector string: [0.1,0.2,...] → list of floats
        vec_str = r[1].strip("[]")
        vec = [float(x) for x in vec_str.split(",")]
        vectors.append(vec)

    return ids, np.array(vectors, dtype=np.float32)


def _kmeans(vectors: np.ndarray, k: int, max_iter: int = 50,
            seed: int = 42) -> tuple:
    """Simple k-means clustering (no sklearn dependency).

    Returns (labels, centroids) where:
        labels: array of cluster assignments (0 to k-1)
        centroids: array of shape (k, dims)
    """
    rng = np.random.RandomState(seed)
    n, dims = vectors.shape

    # Initialize centroids with k-means++
    centroids = np.empty((k, dims), dtype=np.float32)
    centroids[0] = vectors[rng.randint(n)]

    for i in range(1, k):
        dists = np.min([
            np.sum((vectors - centroids[j]) ** 2, axis=1)
            for j in range(i)
        ], axis=0)
        probs = dists / dists.sum()
        centroids[i] = vectors[rng.choice(n, p=probs)]

    # Iterate
    labels = np.zeros(n, dtype=np.int32)
    for iteration in range(max_iter):
        # Assign
        dists = np.array([
            np.sum((vectors - centroids[j]) ** 2, axis=1)
            for j in range(k)
        ])  # shape (k, n)
        new_labels = np.argmin(dists, axis=0)

        # Check convergence
        if np.all(new_labels == labels):
            logger.info(f"K-means converged at iteration {iteration}")
            break
        labels = new_labels

        # Update centroids
        for j in range(k):
            mask = labels == j
            if mask.any():
                centroids[j] = vectors[mask].mean(axis=0)

    return labels, centroids


def _coherence_score(vectors: np.ndarray, labels: np.ndarray,
                      centroids: np.ndarray) -> list:
    """Calculate coherence (avg cosine similarity to centroid) per cluster."""
    k = len(centroids)
    scores = []

    for j in range(k):
        mask = labels == j
        if not mask.any():
            scores.append(0.0)
            continue

        cluster_vecs = vectors[mask]
        centroid = centroids[j]

        # Cosine similarity
        norms_v = np.linalg.norm(cluster_vecs, axis=1, keepdims=True)
        norm_c = np.linalg.norm(centroid)

        if norm_c == 0:
            scores.append(0.0)
            continue

        sims = (cluster_vecs @ centroid) / (norms_v.flatten() * norm_c + 1e-10)
        scores.append(float(np.mean(sims)))

    return scores


def _auto_name_cluster(conn, member_ids: list, max_entries: int = 5) -> str:
    """Generate a name for the cluster from its top entries."""
    if not member_ids:
        return "empty_cluster"

    sample_ids = member_ids[:max_entries]
    placeholders = ",".join(["%s"] * len(sample_ids))

    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT scope, tipo, seccion FROM knowledge_base
            WHERE id IN ({placeholders})
            LIMIT {max_entries}
        """, sample_ids)
        rows = cur.fetchall()

    # Collect most common scope and tipo
    scopes = [r[0] for r in rows if r[0]]
    tipos = [r[1] for r in rows if r[1]]
    secciones = [r[2] for r in rows if r[2]]

    # Most common scope
    from collections import Counter
    top_scope = Counter(scopes).most_common(1)
    top_tipo = Counter(tipos).most_common(1)

    parts = []
    if top_scope:
        parts.append(top_scope[0][0].split("/")[-1])
    if top_tipo:
        parts.append(top_tipo[0][0])
    if secciones:
        parts.append(secciones[0][:30])

    return "_".join(parts)[:100] or "cluster"


def run_clustering(n_clusters: int = 20, conn=None) -> dict:
    """Run k-means on all knowledge_base embeddings and save to knowledge_clusters.

    Args:
        n_clusters: Target number of clusters. Auto-adjusted if too many for data.
        conn: DB connection

    Returns:
        Stats dict with n_clusters, sizes, coherence scores.
    """
    own_conn = conn is None
    if own_conn:
        conn = _get_conn()

    t0 = time.time()
    stats = {"n_clusters": 0, "total_points": 0, "clusters": []}

    try:
        # 1. Load embeddings
        ids, vectors = _load_embeddings(conn)
        if len(ids) == 0:
            return {"error": "Not enough embedded rows", "total_points": 0}

        stats["total_points"] = len(ids)

        # Auto-adjust k if needed
        k = min(n_clusters, len(ids) // 10)  # at least 10 points per cluster
        k = max(k, 2)  # minimum 2 clusters

        logger.info(f"Clustering {len(ids)} points into {k} clusters")

        # 2. Run k-means
        labels, centroids = _kmeans(vectors, k)

        # 3. Calculate coherence
        coherences = _coherence_score(vectors, labels, centroids)

        # 4. Clear old clusters and save new ones
        with conn.cursor() as cur:
            cur.execute("DELETE FROM knowledge_clusters WHERE auto_generated = true")

            for j in range(k):
                mask = labels == j
                member_ids_j = [ids[i] for i in range(len(ids)) if mask[i]]

                if not member_ids_j:
                    continue

                cluster_name = _auto_name_cluster(conn, member_ids_j)
                centroid_vec = centroids[j].tolist()

                cur.execute("""
                    INSERT INTO knowledge_clusters
                        (cluster_name, centroid_embedding, member_ids,
                         coherence_score, auto_generated, updated_at)
                    VALUES (%s, %s::vector, %s, %s, true, NOW())
                """, [
                    cluster_name,
                    str(centroid_vec),
                    member_ids_j,
                    round(coherences[j], 4),
                ])

                stats["clusters"].append({
                    "name": cluster_name,
                    "size": len(member_ids_j),
                    "coherence": round(coherences[j], 4),
                })

        conn.commit()
        stats["n_clusters"] = len(stats["clusters"])
        stats["elapsed_s"] = round(time.time() - t0, 2)

        # Sort by size desc for reporting
        stats["clusters"].sort(key=lambda c: c["size"], reverse=True)

        logger.info(
            f"Clustering complete: {stats['n_clusters']} clusters, "
            f"avg coherence {np.mean(coherences):.3f}, "
            f"{stats['elapsed_s']}s"
        )

        return stats

    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return {"error": str(e)}
    finally:
        if own_conn:
            conn.close()


if __name__ == "__main__":
    import argparse
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    parser = argparse.ArgumentParser(description="Auto-cluster knowledge_base")
    parser.add_argument("--n-clusters", type=int, default=20, help="Target clusters")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    stats = run_clustering(n_clusters=args.n_clusters)
    print(json.dumps(stats, indent=2, default=str))
