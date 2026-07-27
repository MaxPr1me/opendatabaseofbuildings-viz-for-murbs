"""MURB classification module — evidence-based building type classification.

Provides confidence-scored classification of buildings as multi-unit
residential using configurable rules and evidence tracking.
"""

from murb_geometry.classification.classifier import classify_building, normalize_type_value

__all__ = ["classify_building", "normalize_type_value"]
