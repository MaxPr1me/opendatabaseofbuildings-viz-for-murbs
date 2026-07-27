"""Unit tests for building data models."""

from murb_geometry.models.building import (
    BuildingRecord,
    ConfidenceLevel,
    ProvenanceRecord,
    ValueSource,
)


def test_provenance_record_creation() -> None:
    """ProvenanceRecord can be instantiated with minimal fields."""
    prov = ProvenanceRecord(
        original_building_id="abc123",
        province_territory="NS",
        source_organization="Halifax Regional Municipality",
        original_dataset_name="Building Footprints",
        input_file_name="ODB_v3_NS.gpkg",
        input_layer_name="ODB_v3_NS",
    )
    assert prov.province_territory == "NS"


def test_building_record_defaults() -> None:
    """BuildingRecord defaults to insufficient information."""
    prov = ProvenanceRecord(
        original_building_id="test",
        province_territory="ON",
        source_organization="Test",
        original_dataset_name="Test",
        input_file_name="test.gpkg",
        input_layer_name="test",
    )
    record = BuildingRecord(id="test", provenance=prov)
    assert record.classification == ConfidenceLevel.INSUFFICIENT_INFORMATION
    assert record.geometry_metrics is None


def test_value_source_enum() -> None:
    """ValueSource enum contains expected values."""
    assert ValueSource.OBSERVED == "observed"
    assert ValueSource.CALCULATED == "calculated"
    assert ValueSource.ESTIMATED == "estimated"
