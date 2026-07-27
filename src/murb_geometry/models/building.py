"""Core domain models for building records and provenance."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ConfidenceLevel(StrEnum):
    """MURB classification confidence levels."""

    CONFIRMED_MURB = "confirmed_murb"
    HIGH_CONFIDENCE_MURB = "high_confidence_murb"
    PROBABLE_MURB = "probable_murb"
    POSSIBLE_MURB = "possible_murb"
    NON_MURB = "non_murb"
    INSUFFICIENT_INFORMATION = "insufficient_information"


class ValueSource(StrEnum):
    """Origin of a data value."""

    OBSERVED = "observed"
    CALCULATED = "calculated"
    ENRICHED = "enriched"
    ESTIMATED = "estimated"
    IMPUTED = "imputed"
    ASSUMED = "assumed"
    USER_SPECIFIED = "user_specified"


class ProvenanceRecord(BaseModel):
    """Provenance metadata for a building record."""

    original_building_id: str
    province_territory: str
    census_subdivision_id: str | None = None
    census_subdivision_name: str | None = None
    source_organization: str
    original_dataset_name: str
    source_url: str | None = None
    source_publication_date: str | None = None
    source_update_date: str | None = None
    statcan_version: str = "v3"
    input_file_name: str
    input_layer_name: str
    processing_timestamp: datetime | None = None
    processing_software_version: str | None = None
    processing_rule_version: str | None = None


class ClassificationEvidence(BaseModel):
    """Evidence supporting a MURB classification decision."""

    source_field: str
    original_value: str | None = None
    normalized_value: str | None = None
    classification_rule: str
    confidence_score: float | None = None
    evidence_used: list[str] = Field(default_factory=list)
    source_organization: str | None = None
    source_dataset: str | None = None
    processing_date: datetime | None = None
    software_version: str | None = None


class GeometryMetrics(BaseModel):
    """Calculated geometry metrics for a building footprint."""

    footprint_area_m2: float | None = None
    perimeter_m: float | None = None
    mrr_length_m: float | None = None
    mrr_width_m: float | None = None
    aspect_ratio: float | None = None
    orientation_deg: float | None = None
    convex_hull_area_m2: float | None = None
    convexity: float | None = None
    rectangularity: float | None = None
    compactness: float | None = None
    hole_count: int = 0
    hole_area_m2: float = 0.0
    component_count: int = 1
    vertex_count: int | None = None
    simplified_vertex_count: int | None = None


class BuildingRecord(BaseModel):
    """Core building record combining source data with derived fields."""

    id: str
    provenance: ProvenanceRecord
    geometry_metrics: GeometryMetrics | None = None
    classification: ConfidenceLevel = ConfidenceLevel.INSUFFICIENT_INFORMATION
    classification_evidence: list[ClassificationEvidence] = Field(default_factory=list)
    shape_class: str | None = None
    storey_band: str | None = None

    # Original fields (preserved as-is)
    original_type: str | None = None
    original_units: str | None = None
    original_floors: str | None = None
    original_height: str | None = None
    original_sq_ft: str | None = None
    original_year_built: str | None = None

    # Normalized numeric fields
    units_numeric: int | None = None
    floors_numeric: int | None = None
    height_numeric: float | None = None
    year_built_numeric: int | None = None
    sq_ft_numeric: float | None = None

    # Value sources
    units_source: ValueSource | None = None
    floors_source: ValueSource | None = None
    height_source: ValueSource | None = None

    # Arbitrary extra fields from enrichment
    extra: dict[str, Any] = Field(default_factory=dict)
