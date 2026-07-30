"""Unit tests for MURB classification."""

from murb_geometry.classification.classifier import (
    ClassificationResult,
    classify_building,
    normalize_type_value,
)

# --- Tests: normalize_type_value (data-derived mapping, real observed values) ---


def test_normalize_apartment() -> None:
    """Apartment types normalize correctly (real observed values)."""
    assert normalize_type_value("Apartment") == "apartment"
    assert normalize_type_value("High Rise Apartment") == "apartment"
    assert normalize_type_value("low rise apartment") == "apartment"  # case-insensitive


def test_normalize_multi_residential() -> None:
    """Multi-residential types normalize correctly (real observed values)."""
    assert normalize_type_value("MultiFamily") == "multi_residential"
    assert normalize_type_value("Multi-Family Dwelling") == "multi_residential"


def test_normalize_french_residential() -> None:
    """French Quebec type values normalize (previously silently dropped)."""
    assert normalize_type_value("Résidence") == "residential"
    assert normalize_type_value("Résidentielle") == "residential"
    assert normalize_type_value("Résidentiel et commercial") == "mixed_use"


def test_normalize_low_rise_and_single() -> None:
    """Low-rise multi and single-family map to non-MURB categories."""
    assert normalize_type_value("Duplex") == "low_rise_residential"
    assert normalize_type_value("Two Unit Dwelling") == "low_rise_residential"
    assert normalize_type_value("Single Family Dwelling") == "residential_single"


def test_normalize_non_residential() -> None:
    """Non-residential types normalize correctly."""
    assert normalize_type_value("Commercial") == "commercial"
    assert normalize_type_value("Industrial") == "industrial"


def test_normalize_missing_values() -> None:
    """Missing values return None."""
    assert normalize_type_value(None) is None
    assert normalize_type_value("..") is None
    assert normalize_type_value("") is None


def test_normalize_unknown_value() -> None:
    """Genuinely ambiguous / unmapped values return None."""
    assert normalize_type_value("Something Weird") is None
    assert normalize_type_value("General") is None


# --- Tests: classify_building (NBC Part 3 MURB semantics) ---


def test_classify_murb_type_unverified() -> None:
    """MURB-intent type without storey/unit corroboration -> potential (possible) MURB."""
    result = classify_building(type_normalized="apartment")
    assert result.confidence_level == "possible_murb"
    assert result.rule_id == "R005"
    assert "type" in result.evidence_fields


def test_classify_murb_type_storey_verified() -> None:
    """MURB-intent type + 4+ storeys -> confirmed MURB."""
    result = classify_building(type_normalized="apartment", floors_numeric=6)
    assert result.confidence_level == "confirmed_murb"
    assert result.confidence_score == 1.0
    assert result.rule_id == "R001"
    assert "floors" in result.evidence_fields


def test_classify_murb_type_unit_verified() -> None:
    """MURB-intent type + 4+ units -> confirmed MURB."""
    result = classify_building(type_normalized="condominium", units_numeric=8)
    assert result.confidence_level == "confirmed_murb"
    assert result.rule_id == "R001"
    assert "units" in result.evidence_fields


def test_classify_high_unit_count() -> None:
    """High unit count (no MURB type) -> high confidence MURB."""
    result = classify_building(units_numeric=12)
    assert result.confidence_level == "high_confidence_murb"
    assert result.confidence_score == 0.85
    assert result.rule_id == "R003"


def test_classify_unit_count_below_threshold() -> None:
    """Unit count below threshold does not trigger the unit rule."""
    result = classify_building(units_numeric=2)
    assert result.rule_id != "R003"


def test_classify_storey_verified_part3() -> None:
    """4+ storeys with residential/unknown context -> high confidence MURB."""
    result = classify_building(floors_numeric=5, footprint_area_m2=600.0)
    assert result.confidence_level == "high_confidence_murb"
    assert result.rule_id == "R002"


def test_classify_large_residential_footprint() -> None:
    """Large residential footprint is a weak signal -> possible MURB."""
    result = classify_building(
        footprint_area_m2=800.0,
        type_normalized="residential",
    )
    assert result.confidence_level == "possible_murb"
    assert result.rule_id == "R006"


def test_classify_tall_building() -> None:
    """Height >= threshold is a Part 3 storey proxy -> probable MURB."""
    result = classify_building(height_numeric=15.0)
    assert result.confidence_level == "probable_murb"
    assert result.rule_id == "R004"


def test_classify_explicit_non_murb() -> None:
    """Non-residential type -> non_murb."""
    result = classify_building(type_normalized="commercial")
    assert result.confidence_level == "non_murb"
    assert result.rule_id == "R010"


def test_classify_low_rise_type_excluded() -> None:
    """Low-rise multi (e.g. fourplex) is non-MURB even with 4 units (Part 9)."""
    result = classify_building(type_normalized="low_rise_residential", units_numeric=4)
    assert result.confidence_level == "non_murb"
    assert result.rule_id == "R010"


def test_classify_small_footprint() -> None:
    """Small footprint -> non_murb."""
    result = classify_building(footprint_area_m2=80.0)
    assert result.confidence_level == "non_murb"
    assert result.rule_id == "R011"


def test_classify_no_information() -> None:
    """No data -> insufficient information."""
    result = classify_building()
    assert result.confidence_level == "insufficient_information"
    assert result.confidence_score is None
    assert result.rule_id == "R999"


def test_classify_priority_order() -> None:
    """MURB type corroborated by units -> confirmed via R001 (wins over R003)."""
    result = classify_building(type_normalized="apartment", units_numeric=20)
    assert result.rule_id == "R001"


def test_classify_preserves_evidence() -> None:
    """Classification result preserves evidence chain."""
    result = classify_building(
        type_normalized="condominium",
        units_numeric=50,
        floors_numeric=15,
    )
    assert isinstance(result, ClassificationResult)
    assert result.reasoning != ""
    assert len(result.evidence_fields) > 0


def test_classify_custom_thresholds() -> None:
    """Custom thresholds are respected."""
    # 3 units with default threshold (4) -> not a unit-verified MURB
    result_default = classify_building(units_numeric=3)
    assert result_default.rule_id != "R003"

    # 3 units with threshold of 3 -> high confidence
    result_custom = classify_building(units_numeric=3, min_murb_units=3)
    assert result_custom.confidence_level == "high_confidence_murb"
    assert result_custom.rule_id == "R003"
