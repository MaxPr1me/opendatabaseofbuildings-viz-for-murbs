"""External data enrichment module — authoritative source integration.

Provides a framework for enriching building records with external
authoritative data (height, storeys, units, age, etc.).
"""

from murb_geometry.enrichment.framework import EnrichmentSource, apply_enrichment

__all__ = ["EnrichmentSource", "apply_enrichment"]
