"""Descriptive statistics for building geometry distributions.

Reports: count, valid_count, missingness, min, max, mean, median,
std, P5, P10, P25, P75, P90, P95, IQR as required by the methodology.
"""

import numpy as np
from numpy.typing import NDArray


def compute_descriptive_stats(
    values: list[float] | NDArray,
    field_name: str = "",
) -> dict[str, float | int | str]:
    """Compute standard descriptive statistics for a numeric array.

    Parameters
    ----------
    values
        Array of numeric values (may include NaN for missing).
    field_name
        Name of the field being summarized.

    Returns
    -------
    dict
        Statistics dictionary with count, valid_count, missingness,
        min, max, mean, median, std, and percentiles.
    """
    arr = np.asarray(values, dtype=float)
    total_count = len(arr)
    valid = arr[~np.isnan(arr)]
    valid_count = len(valid)
    missing_count = total_count - valid_count
    missingness_pct = (100.0 * missing_count / total_count) if total_count > 0 else 0.0

    if valid_count == 0:
        return {
            "field": field_name,
            "count": total_count,
            "valid_count": 0,
            "missing_count": missing_count,
            "missingness_pct": missingness_pct,
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
            "std": None,
            "p5": None,
            "p10": None,
            "p25": None,
            "p75": None,
            "p90": None,
            "p95": None,
            "iqr": None,
        }

    p5, p10, p25, p50, p75, p90, p95 = np.percentile(valid, [5, 10, 25, 50, 75, 90, 95])

    return {
        "field": field_name,
        "count": total_count,
        "valid_count": valid_count,
        "missing_count": missing_count,
        "missingness_pct": round(missingness_pct, 2),
        "min": float(np.min(valid)),
        "max": float(np.max(valid)),
        "mean": round(float(np.mean(valid)), 2),
        "median": float(p50),
        "std": round(float(np.std(valid, ddof=1)), 2) if valid_count > 1 else 0.0,
        "p5": float(p5),
        "p10": float(p10),
        "p25": float(p25),
        "p75": float(p75),
        "p90": float(p90),
        "p95": float(p95),
        "iqr": float(p75 - p25),
    }
