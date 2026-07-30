"""Tests for the processed MURB-subset data store."""

import geopandas as gpd
import pytest
from shapely.geometry import box

from murb_geometry import datastore
from murb_geometry.datastore import ProcessedDataUnavailableError


@pytest.fixture
def sample_subset() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {
            "confidence_level": ["confirmed_murb", "possible_murb"],
            "_province": ["NS", "ON"],
            "footprint_area_m2": [600.0, 800.0],
            "geometry": [box(0, 0, 20, 30), box(0, 0, 40, 20)],
        },
        geometry="geometry",
        crs="EPSG:3347",
    )


def test_write_and_load_roundtrip(tmp_path, sample_subset) -> None:
    datastore.write_murb_subset(sample_subset, "tiered", base=tmp_path)
    loaded = datastore.load_murb_subset("tiered", base=tmp_path)
    assert len(loaded) == 2
    assert set(loaded["_province"]) == {"NS", "ON"}


def test_manifest_records_provenance(tmp_path, sample_subset) -> None:
    prov = {"classification": {"minimum_murb_storeys": 4}, "type_normalization_sha256": "abc"}
    datastore.write_murb_subset(sample_subset, "precision", base=tmp_path, provenance=prov)
    manifest = datastore.load_subset_manifest("precision", base=tmp_path)
    assert manifest is not None
    assert manifest["n_rows"] == 2
    assert sorted(manifest["provinces"]) == ["NS", "ON"]
    assert manifest["provenance"] == prov


def test_load_missing_raises(tmp_path) -> None:
    with pytest.raises(ProcessedDataUnavailableError):
        datastore.load_murb_subset("tiered", base=tmp_path)


def test_empty_subset_no_parquet_but_manifest(tmp_path) -> None:
    empty = gpd.GeoDataFrame({"geometry": []}, geometry="geometry", crs="EPSG:3347")
    datastore.write_murb_subset(empty, "precision", base=tmp_path)
    assert not datastore.subset_available("precision", base=tmp_path)
    manifest = datastore.load_subset_manifest("precision", base=tmp_path)
    assert manifest is not None
    assert manifest["n_rows"] == 0
    with pytest.raises(ProcessedDataUnavailableError):
        datastore.load_murb_subset("precision", base=tmp_path)


def test_is_subset_valid_detects_stale(tmp_path, sample_subset) -> None:
    datastore.write_murb_subset(sample_subset, "tiered", base=tmp_path, provenance={"v": 1})
    valid, reasons = datastore.is_subset_valid(
        "tiered", base=tmp_path, expected_provenance={"v": 1}
    )
    assert valid is True
    assert reasons == []

    stale, reasons2 = datastore.is_subset_valid(
        "tiered", base=tmp_path, expected_provenance={"v": 2}
    )
    assert stale is False
    assert any("provenance mismatch" in r for r in reasons2)


def test_subset_status(tmp_path, sample_subset) -> None:
    datastore.write_murb_subset(sample_subset, "tiered", base=tmp_path, provenance={"v": 1})
    status = datastore.subset_status(base=tmp_path, expected_provenance={"v": 1})
    assert status["tiered"]["available"] is True
    assert status["tiered"]["valid"] is True
    assert status["tiered"]["n_rows"] == 2
    assert status["precision"]["available"] is False


def test_unknown_pathway_raises() -> None:
    with pytest.raises(ValueError, match="Unknown pathway"):
        datastore.subset_path("bogus")


def test_drop_geometry(tmp_path, sample_subset) -> None:
    datastore.write_murb_subset(sample_subset, "tiered", base=tmp_path)
    df = datastore.load_murb_subset("tiered", base=tmp_path, drop_geometry=True)
    assert "geometry" not in df.columns
    assert len(df) == 2
