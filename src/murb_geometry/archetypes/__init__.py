"""Archetype derivation module — clustering, medoids, and synthetic geometry.

Provides methods to derive representative MURB archetypes from the
building population, including medoid selection and parametric synthesis.
"""

from murb_geometry.archetypes.selection import select_medoid

__all__ = ["select_medoid"]
