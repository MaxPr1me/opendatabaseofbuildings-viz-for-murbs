"""MURB classification engine.

Applies evidence-based rules to classify buildings with confidence scores.
Every classification preserves its evidence chain for auditability.

MURB definition (owner decision, 2026-07-30): NBC Part 3 multi-unit residential
(4+ storeys, or > 600 m2 building area). Part 9 low-rise (duplex, semi-detached,
townhouse, row, two-unit, single-family) is NOT a MURB. An explicit
apartment/multi-residential/condominium ``type`` confirms a MURB only when a storey
or unit check corroborates it; otherwise such types are flagged as potential
(possible) MURBs. Generic residential requires storey/height/unit evidence.

The type -> category mapping is loaded from ``config/type_normalization.yaml``,
which is generated from the full-population schema audit (no hand-invented values).
"""

from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

import yaml

# Category taxonomy — mirrors config/type_normalization.yaml.
MURB_INTENT_CATEGORIES = frozenset({"apartment", "multi_residential", "condominium"})
EXPLICIT_NON_MURB_CATEGORIES = frozenset(
    {
        "residential_single",
        "low_rise_residential",
        "commercial",
        "industrial",
        "institutional",
        "other",
    }
)
RESIDENTIAL_CONTEXT_CATEGORIES = frozenset({"residential", "mixed_use"})

_DEFAULT_MAPPING_PATH = "config/type_normalization.yaml"


@cache
def _load_type_mapping(path: str = _DEFAULT_MAPPING_PATH) -> dict[str, str]:
    """Load the value -> category mapping from the normalization config.

    Returns a dict keyed by lower-cased, trimmed source value. Cached so the
    file is parsed once per path. Returns an empty mapping if the file is absent.
    """
    p = Path(path)
    if not p.exists():
        return {}
    doc = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    mapping: dict[str, str] = {}
    for category, values in (doc.get("mapping") or {}).items():
        for value in values or []:
            key = str(value).strip().lower()
            if key:
                mapping[key] = str(category)
    return mapping


def normalize_type_value(
    raw_value: str | None,
    mapping_path: str = _DEFAULT_MAPPING_PATH,
) -> str | None:
    """Normalize a source-specific building type value to a canonical category.

    The mapping is data-derived (``config/type_normalization.yaml``). Values not
    present in the mapping (genuinely ambiguous or long-tail) return None.

    Parameters
    ----------
    raw_value
        Original type field value from the database.
    mapping_path
        Path to the normalization config (default: config/type_normalization.yaml).

    Returns
    -------
    str | None
        Normalized category, or None if the value is missing/unmapped.
    """
    if raw_value is None:
        return None
    key = str(raw_value).strip().lower()
    if key in ("", ".."):
        return None
    return _load_type_mapping(mapping_path).get(key)


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
    min_murb_storeys: int = 4,
    murb_height_threshold_m: float = 12.0,
    large_footprint_m2: float = 600.0,
    min_candidate_area_m2: float = 200.0,
) -> ClassificationResult:
    """Classify a building as a Part 3 MURB with a confidence level.

    Rules are evaluated in priority order; the first match wins. See the module
    docstring for the MURB definition and rationale.

    Parameters
    ----------
    type_normalized
        Normalized building type category (see :func:`normalize_type_value`).
    units_numeric
        Number of dwelling units (parsed from source), if known.
    floors_numeric
        Number of storeys (parsed from source), if known.
    footprint_area_m2
        Building footprint area in square metres.
    height_numeric
        Building height in metres, if known.
    min_murb_units
        Minimum dwelling units for a unit-verified MURB (default: 4).
    min_murb_storeys
        Minimum storeys for a Part 3 MURB (default: 4).
    murb_height_threshold_m
        Height (m) treated as a proxy for Part 3 storey count (default: 12).
    large_footprint_m2
        Footprint (m2) treated as a weak MURB signal for residential context
        (default: 600).
    min_candidate_area_m2
        Minimum footprint area for any geometric MURB candidate (default: 200).

    Returns
    -------
    ClassificationResult
        Classification with confidence level, score, rule, and evidence.
    """
    has_storeys = floors_numeric is not None and floors_numeric >= min_murb_storeys
    has_units = units_numeric is not None and units_numeric >= min_murb_units
    is_murb_intent = type_normalized in MURB_INTENT_CATEGORIES
    is_residential_context = type_normalized in RESIDENTIAL_CONTEXT_CATEGORIES
    area_ok = footprint_area_m2 is None or footprint_area_m2 >= min_candidate_area_m2

    # Rule R010: Explicit non-MURB type (single-family, low-rise multi, non-residential).
    if type_normalized in EXPLICIT_NON_MURB_CATEGORIES:
        return ClassificationResult(
            confidence_level="non_murb",
            confidence_score=0.0,
            rule_id="R010",
            rule_name="explicit_non_murb_type",
            evidence_fields=["type"],
            reasoning=f"Type '{type_normalized}' is single-family, low-rise, or non-residential",
        )

    # Rule R001: MURB-intent type corroborated by storeys or units -> confirmed.
    if is_murb_intent and (has_storeys or has_units):
        evidence = ["type"]
        parts: list[str] = []
        if has_storeys:
            evidence.append("floors")
            parts.append(f"floors ({floors_numeric}) >= {min_murb_storeys}")
        if has_units:
            evidence.append("units")
            parts.append(f"units ({units_numeric}) >= {min_murb_units}")
        return ClassificationResult(
            confidence_level="confirmed_murb",
            confidence_score=1.0,
            rule_id="R001",
            rule_name="murb_type_storey_unit_verified",
            evidence_fields=evidence,
            reasoning=f"MURB type '{type_normalized}' corroborated by " + " and ".join(parts),
        )

    # Rule R002: Storeys >= threshold with residential/unknown context -> high confidence.
    if has_storeys and area_ok:
        return ClassificationResult(
            confidence_level="high_confidence_murb",
            confidence_score=0.85,
            rule_id="R002",
            rule_name="storey_verified_part3",
            evidence_fields=["floors"],
            reasoning=f"Floors ({floors_numeric}) >= {min_murb_storeys} (Part 3 storey scale)",
        )

    # Rule R003: Dwelling units >= threshold -> high confidence.
    if has_units:
        return ClassificationResult(
            confidence_level="high_confidence_murb",
            confidence_score=0.85,
            rule_id="R003",
            rule_name="unit_verified",
            evidence_fields=["units"],
            reasoning=f"Unit count ({units_numeric}) >= threshold ({min_murb_units})",
        )

    # Rule R004: Height proxy for Part 3 storey count -> probable.
    if height_numeric is not None and height_numeric >= murb_height_threshold_m and area_ok:
        return ClassificationResult(
            confidence_level="probable_murb",
            confidence_score=0.70,
            rule_id="R004",
            rule_name="height_proxy_part3",
            evidence_fields=["height"],
            reasoning=(
                f"Height ({height_numeric:.1f} m) >= {murb_height_threshold_m:.0f} m "
                "suggests Part 3 storey count"
            ),
        )

    # Rule R005: MURB-intent type without storey/unit corroboration -> potential MURB.
    if is_murb_intent:
        return ClassificationResult(
            confidence_level="possible_murb",
            confidence_score=0.50,
            rule_id="R005",
            rule_name="murb_type_unverified",
            evidence_fields=["type"],
            reasoning=(
                f"MURB type '{type_normalized}' without storey/unit corroboration -> potential MURB"
            ),
        )

    # Rule R006: Large residential footprint (weak signal; storey data preferred) -> possible.
    if (
        is_residential_context
        and footprint_area_m2 is not None
        and footprint_area_m2 >= large_footprint_m2
    ):
        return ClassificationResult(
            confidence_level="possible_murb",
            confidence_score=0.45,
            rule_id="R006",
            rule_name="large_residential_footprint",
            evidence_fields=["footprint_area_m2", "type"],
            reasoning=(
                f"Large residential footprint ({footprint_area_m2:.0f} m2) >= "
                f"{large_footprint_m2:.0f} m2 (weak signal; storey/height preferred)"
            ),
        )

    # Rule R011: Small footprint (unlikely MURB) -> non_murb.
    if footprint_area_m2 is not None and footprint_area_m2 < min_candidate_area_m2:
        return ClassificationResult(
            confidence_level="non_murb",
            confidence_score=0.0,
            rule_id="R011",
            rule_name="small_footprint",
            evidence_fields=["footprint_area_m2"],
            reasoning=(
                f"Footprint ({footprint_area_m2:.0f} m2) below minimum candidate "
                f"threshold ({min_candidate_area_m2:.0f} m2)"
            ),
        )

    # Default: insufficient information.
    return ClassificationResult(
        confidence_level="insufficient_information",
        confidence_score=None,
        rule_id="R999",
        rule_name="no_matching_rule",
        evidence_fields=[],
        reasoning="No classification rule matched with available evidence",
    )
