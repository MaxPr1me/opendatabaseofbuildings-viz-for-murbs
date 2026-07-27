"""Geometry validation module — CRS checks, repair, and quality flags.

Provides functions to validate building footprint geometries and
produce quality flags without modifying original data.
"""

from murb_geometry.validation.geometry import validate_geometry

__all__ = ["validate_geometry"]
