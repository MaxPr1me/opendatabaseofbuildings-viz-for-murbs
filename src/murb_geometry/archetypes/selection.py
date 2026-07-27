"""Archetype selection — medoid and representative building identification.

Selects the most representative actual building from a set based on
proximity to the cluster centroid in feature space.
"""

import numpy as np
from numpy.typing import NDArray


def select_medoid(features: NDArray) -> int:
    """Select the medoid (most central point) from a feature matrix.

    The medoid is the point with minimum sum of distances to all other
    points — the most representative actual building in the set.

    Parameters
    ----------
    features
        2D array of shape (n_samples, n_features). Should be normalized.

    Returns
    -------
    int
        Index of the medoid in the feature array.

    Raises
    ------
    ValueError
        If features array is empty.
    """
    if features.size == 0:
        raise ValueError("Cannot select medoid from empty feature array")

    features = np.asarray(features, dtype=float)
    if features.ndim == 1:
        features = features.reshape(-1, 1)

    n = features.shape[0]
    if n == 1:
        return 0

    # Compute pairwise squared distances
    # Using broadcasting: ||a - b||^2 = ||a||^2 + ||b||^2 - 2*a.b
    sq_norms = np.sum(features**2, axis=1)
    dist_matrix = sq_norms[:, np.newaxis] + sq_norms[np.newaxis, :] - 2 * features @ features.T
    np.clip(dist_matrix, 0, None, out=dist_matrix)  # numerical stability

    # Sum of distances for each point
    total_distances = np.sum(np.sqrt(dist_matrix), axis=1)

    return int(np.argmin(total_distances))
