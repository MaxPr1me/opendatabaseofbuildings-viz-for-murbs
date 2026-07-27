"""MURB classification engine.

Applies evidence-based rules to classify buildings with confidence scores.
Every classification preserves its evidence chain for auditability.
"""

from dataclasses import dataclass, field

# Type normalization mapping — maps source-specific values to standard categories
_TYPE_NORMALIZATION: dict[str, str] = {
    # Apartment/MURB indicators
    "apartment": "apartment",
    "apartment building": "apartment",
    "apt": "apartment",
    "multi-residential": "multi_residential",
    "multi residential": "multi_residential",
    "residential - multi": "multi_residential",
    "residential-multi": "multi_residential",
    "multiple dwelling": "multi_residential",
    "multiple residential": "multi_residential",
    "condominium": "condominium",
    "condo": "condominium",
    "high rise apartment": "apartment",
    "high-rise apartment": "apartment",
    "low rise apartment": "apartment",
    "low-rise apartment": "apartment",
    "walk-up apartment": "apartment",
    "walkup apartment": "apartment",
    "row housing": "row_housing",
    "row house": "row_housing",
    "townhouse": "townhouse",
    "semi-detached": "semi_detached",
    # Single-family indicators
    "residential": "residential",
    "residential - single": "residential_single",
    "single family": "residential_single",
    "single family dwelling": "residential_single",
    "detached": "residential_single",
    "house": "residential_single",
    # Non-residential
    "commercial": "commercial",
    "industrial": "industrial",
    "institutional": "institutional",
    "mixed use": "mixed_use",
    "mixed-use": "mixed_use",
    "retail": "commercial",
    "office": "commercial",
    "church": "institutional",
    "school": "institutional",
    "hospital": "institutional",
    "government": "institutional",
    "park": "other",
    "garage": "other",
    "shed": "other",
    "barn": "other",
    "agricultural": "other",
}


def normalize_type_value(raw_value: str | None) -> str | None:
    """Normalize a source-specific building type value.

    Parameters
    ----------
    raw_value
        Original type field value from the database.

    Returns
    -------
    str | None
        Normalized category, or None if the value is missing/unmapped.
    """
    if raw_value is None or raw_value.strip() in ("", ".."):
        return None
    key = raw_value.strip().lower()
    return _TYPE_NORMALIZATION.get(key)


@dataclass
class ClassificationResult:
    """Result of classifying a single building."""

    confidence_level: str
    confidence_score: float | None
    rule_id: str
    rule_name: str
    evidence_fields: list[str] = field(default_factory=list)
    reasoning: str = ""


def classify_building(
    type_normalized: str | None = None,
    units_numeric: int | None = None,
    floors_numeric: int | None = None,
    footprint_area_m2: float | None = None,
    height_numeric: float | None = None,
    *,
    min_murb_units: int = 4,
    min_candidate_area_m2: float = 200.0,
) -> ClassificationResult:
    """Classify a building as MURB with confidence level.

    Rules are evaluated in priority order; first match wins.
    Preserves evidence for auditability.

    Parameters
    ----------
    type_normalized
        Normalized building type string.
    units_numeric
        Number of dwelling units (parsed from source).
    floors_numeric
        Number of storeys (parsed from source).
    footprint_area_m2
        Building footprint area in square metres.
    height_numeric
        Building height in metres.
    min_murb_units
        Minimum units to qualify as MURB (default: 4).
    min_candidate_area_m2
        Minimum footprint area for geometric candidates (default: 200).

    Returns
    -------
    ClassificationResult
        Classification with confidence level, score, rule, and evidence.
    """
    # Rule R001: Explicit apartment/multi-residential type
    if type_normalized in ("apartment", "multi_residential", "condominium"):
        return ClassificationResult(
            confidence_level="confirmed_murb",
            confidence_score=1.0,
            rule_id="R001",
            rule_name="explicit_apartment_type",
            evidence_fields=["type"],
            reasoning=f"Type '{type_normalized}' explicitly identifies multi-unit residential",
        )

    # Rule R002: High unit count
    if units_numeric is not None and units_numeric >= min_murb_units:
        return ClassificationResult(
            confidence_level="high_confidence_murb",
            confidence_score=0.85,
            rule_id="R002",
            rule_name="high_unit_count",
            evidence_fields=["units"],
            reasoning=f"Unit count ({units_numeric}) >= threshold ({min_murb_units})",
        )

    # Rule R003: Multi-floor + large footprint
    if (
        floors_numeric is not None
        and floors_numeric >= 4
        and footprint_area_m2 is not None
        and footprint_area_m2 >= 400
    ):
        return ClassificationResult(
            confidence_level="probable_murb",
            confidence_score=0.70,
            rule_id="R003",
            rule_name="multi_floor_large_footprint",
            evidence_fields=["floors", "footprint_area_m2"],
            reasoning=(
                f"Floors ({floors_numeric}) >= 4 and "
                f"area ({footprint_area_m2:.0f} m2) >= 400"
            ),
        )

    # Rule R004: Large footprint + residential context
    if (
        footprint_area_m2 is not None
        and footprint_area_m2 >= 600
        and type_normalized in ("residential", "mixed_use")
    ):
        return ClassificationResult(
            confidence_level="possible_murb",
            confidence_score=0.50,
            rule_id="R004",
            rule_name="large_footprint_residential_context",
            evidence_fields=["footprint_area_m2", "type"],
            reasoning=(
                f"Large residential footprint ({footprint_area_m2:.0f} m2) "
                f"with type '{type_normalized}'"
            ),
        )

    # Rule R005: Tall building (height suggests multi-storey)
    if height_numeric is not None and height_numeric >= 12.0:
        return ClassificationResult(
            confidence_level="possible_murb",
            confidence_score=0.45,
            rule_id="R005",
            rule_name="tall_building",
            evidence_fields=["height"],
            reasoning=f"Building height ({height_numeric:.1f} m) >= 12 m suggests multi-storey",
        )

    # Rule R010: Explicit non-MURB types
    if type_normalized in (
        "residential_single",
        "commercial",
        "industrial",
        "institutional",
        "other",
    ):
        return ClassificationResult(
            confidence_level="non_murb",
            confidence_score=0.0,
            rule_id="R010",
            rule_name="explicit_non_murb_type",
            evidence_fields=["type"],
            reasoning=f"Type '{type_normalized}' is not multi-unit residential",
        )

    # Rule R011: Small footprint (unlikely MURB)
    if footprint_area_m2 is not None and footprint_area_m2 < min_candidate_area_m2:
        return ClassificationResult(
            confidence_level="non_murb",
            confidence_score=0.0,
            rule_id="R011",
            rule_name="small_footprint",
            evidence_fields=["footprint_area_m2"],
            reasoning=(
                f"Footprint ({footprint_area_m2:.0f} m2) below "
                f"minimum candidate threshold ({min_candidate_area_m2} m2)"
            ),
        )

    # Default: insufficient information
    return ClassificationResult(
        confidence_level="insufficient_information",
        confidence_score=None,
        rule_id="R999",
        rule_name="no_matching_rule",
        evidence_fields=[],
        reasoning="No classification rule matched with available evidence",
    )
