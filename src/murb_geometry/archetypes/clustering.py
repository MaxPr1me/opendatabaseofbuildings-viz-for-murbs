"""K-Means clustering for building archetype grouping.

Clusters buildings by geometry features to identify natural groupings,
then selects the medoid of each cluster as the representative building.
"""

import numpy as np
from numpy.typing import NDArray
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from murb_geometry.archetypes.selection import select_medoid


def cluster_buildings(
    features: NDArray[np.floating],
    n_clusters: int = 8,
    random_seed: int = 42,
) -> dict[str, object]:
    """Cluster buildings and select representative medoids.

    Parameters
    ----------
    features
        2D array of shape (n_samples, n_features).
    n_clusters
        Number of archetype clusters to create.
    random_seed
        Random seed for reproducibility.

    Returns
    -------
    dict with keys:
        labels: cluster assignment for each building (array of ints)
        centers: cluster centroids in scaled space
        medoid_indices: index of the medoid building per cluster
        inertia: within-cluster sum of squares
        n_clusters: number of clusters used
    """
    features = np.asarray(features, dtype=float)
    if features.ndim == 1:
        features = features.reshape(-1, 1)

    n_samples = features.shape[0]
    actual_k = min(n_clusters, n_samples)

    # Standardize features
    scaler = StandardScaler()
    scaled = scaler.fit_transform(features)

    # K-Means clustering
    kmeans = KMeans(
        n_clusters=actual_k,
        random_state=random_seed,
        n_init=10,
    )
    labels = kmeans.fit_predict(scaled)

    # Select medoid for each cluster
    medoid_indices: list[int] = []
    for k in range(actual_k):
        cluster_mask = labels == k
        cluster_indices = np.where(cluster_mask)[0]
        cluster_features = scaled[cluster_mask]
        local_medoid = select_medoid(cluster_features)
        medoid_indices.append(int(cluster_indices[local_medoid]))

    return {
        "labels": labels,
        "centers": kmeans.cluster_centers_,
        "medoid_indices": medoid_indices,
        "inertia": float(kmeans.inertia_),
        "n_clusters": actual_k,
    }
