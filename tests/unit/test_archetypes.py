"""Unit tests for archetype selection."""

import numpy as np
import pytest

from murb_geometry.archetypes.selection import select_medoid


def test_medoid_single_point() -> None:
    """Single point is its own medoid."""
    features = np.array([[1.0, 2.0, 3.0]])
    assert select_medoid(features) == 0


def test_medoid_symmetric_cluster() -> None:
    """Centre point is the medoid of a symmetric cluster."""
    features = np.array(
        [
            [0.0, 0.0],
            [1.0, 0.0],
            [0.5, 0.5],  # centre-ish
            [0.0, 1.0],
            [1.0, 1.0],
        ]
    )
    medoid_idx = select_medoid(features)
    # The centre point (0.5, 0.5) should be selected
    assert medoid_idx == 2


def test_medoid_1d() -> None:
    """1D medoid is the median-like point."""
    features = np.array([1.0, 2.0, 3.0, 100.0])
    medoid_idx = select_medoid(features)
    # Point 2 or 3 should be selected (not the outlier 100)
    assert medoid_idx in (1, 2)


def test_medoid_empty_raises() -> None:
    """Empty array raises ValueError."""
    with pytest.raises(ValueError, match="empty"):
        select_medoid(np.array([]))


def test_medoid_deterministic() -> None:
    """Medoid selection is deterministic."""
    rng = np.random.default_rng(42)
    features = rng.random((50, 4))
    idx1 = select_medoid(features)
    idx2 = select_medoid(features)
    assert idx1 == idx2
