"""Geometry processing module — metric extraction and shape analysis.

Provides vectorized functions to compute building footprint metrics
including area, dimensions, aspect ratio, compactness, rectangularity,
convexity, orientation, and facade analysis.
"""

from murb_geometry.geometry.metrics import compute_geometry_metrics

__all__ = ["compute_geometry_metrics"]
