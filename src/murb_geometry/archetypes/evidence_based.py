"""Evidence-based archetype generation with diagnostic-driven cluster selection.

Replaces hard-coded k=5/k=8 with empirical evaluation of multiple k values.
Reports silhouette scores, inertia/elbow, cluster sizes, and stability.
"""

import logging
from typing import Any

import numpy as np
from numpy.typing import NDArray
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from murb_geometry.archetypes.selection import select_medoid

logger = logging.getLogger(__name__)


def evaluate_cluster_range(
    features: NDArray[np.floating],
    k_min: int = 2,
    k_max: int = 15,
    random_seed: int = 42,
    n_init: int = 10,
) -> dict[str, Any]:
    """Evaluate clustering across a range of k values.

    Returns diagnostics for each k: silhouette, inertia, cluster sizes.
    Does NOT select k automatically — provides evidence for informed choice.

    Parameters
    ----------
    features
        2D array of shape (n_samples, n_features).
    k_min
        Minimum number of clusters to evaluate.
    k_max
        Maximum number of clusters to evaluate.
    random_seed
        Random seed for reproducibility.
    n_init
        Number of KMeans initializations per k.

    Returns
    -------
    dict with:
        diagnostics: list of per-k results
        features_shape: (n_samples, n_features)
        recommended_k: k with highest silhouette (advisory, not prescriptive)
    """
    features = np.asarray(features, dtype=float)
    if features.ndim == 1:
        features = features.reshape(-1, 1)

    n_samples = features.shape[0]
    k_max = min(k_max, n_samples - 1)
    k_min = max(k_min, 2)

    scaler = StandardScaler()
    scaled = scaler.fit_transform(features)

    diagnostics: list[dict[str, Any]] = []
    best_silhouette = -1.0
    best_k = k_min

    for k in range(k_min, k_max + 1):
        kmeans = KMeans(n_clusters=k, random_state=random_seed, n_init=n_init)
        labels = kmeans.fit_predict(scaled)

        sil = float(silhouette_score(scaled, labels))
        inertia = float(kmeans.inertia_)

        # Cluster sizes
        sizes = [int(np.sum(labels == i)) for i in range(k)]
        min_size = min(sizes)
        max_size = max(sizes)

        diag = {
            "k": k,
            "silhouette_score": round(sil, 4),
            "inertia": round(inertia, 2),
            "cluster_sizes": sizes,
            "min_cluster_size": min_size,
            "max_cluster_size": max_size,
            "size_ratio": round(max_size / max(min_size, 1), 2),
        }
        diagnostics.append(diag)

        if sil > best_silhouette:
            best_silhouette = sil
            best_k = k

        logger.info(
            "  k=%d: silhouette=%.4f, inertia=%.0f, sizes=%s",
            k,
            sil,
            inertia,
            sizes,
        )

    return {
        "diagnostics": diagnostics,
        "features_shape": features.shape,
        "recommended_k": best_k,
        "best_silhouette": round(best_silhouette, 4),
    }


def generate_archetypes(
    features: NDArray[np.floating],
    n_clusters: int,
    random_seed: int = 42,
    n_init: int = 10,
    n_stability_runs: int = 5,
) -> dict[str, Any]:
    """Generate archetypes with full diagnostics and stability analysis.

    Parameters
    ----------
    features
        2D array (n_samples, n_features).
    n_clusters
        Number of clusters (should be justified by diagnostics).
    random_seed
        Base random seed.
    n_init
        KMeans initializations.
    n_stability_runs
        Number of runs with different seeds to assess stability.

    Returns
    -------
    dict with:
        labels, medoid_indices, centers, inertia, silhouette,
        cluster_sizes, stability_scores, diagnostics
    """
    features = np.asarray(features, dtype=float)
    if features.ndim == 1:
        features = features.reshape(-1, 1)

    n_samples = features.shape[0]
    actual_k = min(n_clusters, n_samples - 1)

    scaler = StandardScaler()
    scaled = scaler.fit_transform(features)

    # Primary clustering
    kmeans = KMeans(n_clusters=actual_k, random_state=random_seed, n_init=n_init)
    labels = kmeans.fit_predict(scaled)
    sil = float(silhouette_score(scaled, labels))

    # Select medoids
    medoid_indices: list[int] = []
    for k in range(actual_k):
        cluster_mask = labels == k
        cluster_indices = np.where(cluster_mask)[0]
        cluster_features = scaled[cluster_mask]
        local_medoid = select_medoid(cluster_features)
        medoid_indices.append(int(cluster_indices[local_medoid]))

    # Cluster sizes and proportions
    sizes = [int(np.sum(labels == i)) for i in range(actual_k)]

    # Stability analysis — run with different seeds
    stability_scores: list[float] = []
    for run in range(n_stability_runs):
        alt_seed = random_seed + run + 1
        alt_kmeans = KMeans(n_clusters=actual_k, random_state=alt_seed, n_init=n_init)
        alt_labels = alt_kmeans.fit_predict(scaled)
        # Measure agreement via adjusted Rand index
        from sklearn.metrics import adjusted_rand_score

        ari = float(adjusted_rand_score(labels, alt_labels))
        stability_scores.append(round(ari, 4))

    mean_stability = round(float(np.mean(stability_scores)), 4)

    logger.info(
        "Archetypes: k=%d, silhouette=%.4f, stability=%.4f, sizes=%s",
        actual_k,
        sil,
        mean_stability,
        sizes,
    )

    return {
        "labels": labels,
        "medoid_indices": medoid_indices,
        "centers": kmeans.cluster_centers_,
        "inertia": float(kmeans.inertia_),
        "silhouette_score": round(sil, 4),
        "n_clusters": actual_k,
        "cluster_sizes": sizes,
        "cluster_proportions": [round(s / n_samples, 4) for s in sizes],
        "stability_scores": stability_scores,
        "mean_stability": mean_stability,
        "n_samples": n_samples,
        "n_features": features.shape[1],
        "random_seed": random_seed,
    }
