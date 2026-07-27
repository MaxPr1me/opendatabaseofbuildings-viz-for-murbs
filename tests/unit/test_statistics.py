"""Unit tests for descriptive statistics."""

import pytest

from murb_geometry.statistics.descriptive import compute_descriptive_stats


def test_basic_stats() -> None:
    """Basic stats are computed correctly."""
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    stats = compute_descriptive_stats(values, field_name="test")
    assert stats["field"] == "test"
    assert stats["count"] == 5
    assert stats["valid_count"] == 5
    assert stats["missing_count"] == 0
    assert stats["min"] == 1.0
    assert stats["max"] == 5.0
    assert stats["mean"] == 3.0
    assert stats["median"] == 3.0


def test_stats_with_nan() -> None:
    """NaN values are treated as missing."""
    values = [1.0, 2.0, float("nan"), 4.0, float("nan")]
    stats = compute_descriptive_stats(values)
    assert stats["count"] == 5
    assert stats["valid_count"] == 3
    assert stats["missing_count"] == 2
    assert stats["missingness_pct"] == 40.0
    assert stats["min"] == 1.0
    assert stats["max"] == 4.0


def test_stats_all_missing() -> None:
    """All-NaN input returns None for all stats."""
    values = [float("nan"), float("nan")]
    stats = compute_descriptive_stats(values)
    assert stats["valid_count"] == 0
    assert stats["mean"] is None
    assert stats["median"] is None
    assert stats["iqr"] is None


def test_stats_empty_input() -> None:
    """Empty input returns zeros."""
    stats = compute_descriptive_stats([])
    assert stats["count"] == 0
    assert stats["valid_count"] == 0


def test_percentiles() -> None:
    """Percentiles are computed."""
    values = list(range(1, 101))  # 1 to 100
    stats = compute_descriptive_stats(values)
    assert stats["p25"] == pytest.approx(25.75, rel=0.1)
    assert stats["median"] == pytest.approx(50.5, rel=0.1)
    assert stats["p75"] == pytest.approx(75.25, rel=0.1)
    assert stats["iqr"] == pytest.approx(49.5, rel=0.1)


def test_iqr_calculation() -> None:
    """IQR = P75 - P25."""
    values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    stats = compute_descriptive_stats(values)
    assert stats["iqr"] == pytest.approx(stats["p75"] - stats["p25"])
