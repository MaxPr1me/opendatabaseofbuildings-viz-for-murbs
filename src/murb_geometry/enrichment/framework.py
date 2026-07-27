"""Enrichment framework for integrating external authoritative data.

Defines the interface and tracking for external data enrichment.
Each enrichment preserves provenance and match confidence.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class EnrichmentSource:
    """Metadata about an external enrichment data source."""

    name: str
    version: str = ""
    provider: str = ""
    access_type: str = "public"  # public, restricted, proprietary
    fields_provided: list[str] = field(default_factory=list)
    match_method: str = ""  # spatial_join, id_match, address_match
    source_date: str = ""
    licence: str = ""
    url: str = ""


@dataclass
class EnrichmentResult:
    """Result of enriching a single building record."""

    building_id: str
    source: EnrichmentSource
    fields_enriched: dict[str, Any] = field(default_factory=dict)
    match_confidence: float = 0.0
    match_method: str = ""
    enrichment_timestamp: str = ""


def apply_enrichment(
    building_id: str,
    source: EnrichmentSource,
    enriched_fields: dict[str, Any],
    match_confidence: float = 1.0,
    match_method: str = "",
) -> EnrichmentResult:
    """Record an enrichment operation for a building.

    Parameters
    ----------
    building_id
        Unique identifier of the building being enriched.
    source
        The enrichment data source metadata.
    enriched_fields
        Dictionary of field_name -> enriched_value.
    match_confidence
        Confidence score for the match [0, 1].
    match_method
        Method used to match the building to the source.

    Returns
    -------
    EnrichmentResult
        Complete enrichment record with provenance.
    """
    return EnrichmentResult(
        building_id=building_id,
        source=source,
        fields_enriched=enriched_fields,
        match_confidence=match_confidence,
        match_method=match_method or source.match_method,
        enrichment_timestamp=datetime.now(UTC).isoformat(),
    )
