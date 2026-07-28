"""Tests for geometry preprocessing and vertical-data modes."""

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import MultiPolygon, Polygon, box

from murb_geometry.validation.preprocessing import (
    HeightSource,
    VerticalDataMode,
    compute_vertical_data,
    preprocess_geometry,
)


@pytest.fixture
def sample_geom_gdf():
    """GeoDataFrame with various geometry conditions."""
    # Valid polygon
    valid = box(0, 0, 30, 20)
    # Invalid polygon (bowtie)
    bowtie = Polygon([(0, 0), (10, 10), (10, 0), (0, 10), (0, 0)])
    # MultiPolygon
    multi = MultiPolygon([box(0, 0, 10, 10), box(20, 20, 30, 30)])
    # Polygon with hole
    outer = box(0, 0, 40, 40)
    hole = box(10, 10, 30, 30)
    with_hole = Polygon(outer.exterior.coords, [hole.exterior.coords])
    # Tiny polygon (implausible)
    tiny = box(0, 0, 0.5, 0.5)

    return gpd.GeoDataFrame(
        {"id": ["valid", "bowtie", "multi", "holed", "tiny", "null"]},
        geometry=[valid, bowtie, multi, with_hole, tiny, None],
        crs="EPSG:3347",
    )


@pytest.fixture
def sample_vertical_gdf():
    """GeoDataFrame with vertical data fields."""
    return gpd.GeoDataFrame(
        {
            "floors_numeric": [4, None, None, 10, 6],
            "height_numeric": [None, 15.0, None, 30.0, 18.0],
            "footprint_area_m2": [500.0, 800.0, 300.0, 1200.0, 600.0],
            "geometry": [box(0, 0, i * 10, 10) for i in range(1, 6)],
        },
        crs="EPSG:3347",
    )


class TestPreprocessGeometry:
    def test_preserves_record_count(self, sample_geom_gdf):
        result = preprocess_geometry(sample_geom_gdf)
        assert len(result) == len(sample_geom_gdf)

    def test_null_geometry_flagged(self, sample_geom_gdf):
        result = preprocess_geometry(sample_geom_gdf)
        null_row = result[result["id"] == "null"].iloc[0]
        assert null_row["geom_is_null"] == True  # noqa: E712

    def test_valid_geometry_passes(self, sample_geom_gdf):
        result = preprocess_geometry(sample_geom_gdf)
        valid_row = result[result["id"] == "valid"].iloc[0]
        assert valid_row["geom_is_valid"] == True  # noqa: E712
        assert valid_row["geom_was_repaired"] == False  # noqa: E712

    def test_invalid_geometry_repaired(self, sample_geom_gdf):
        result = preprocess_geometry(sample_geom_gdf)
        bowtie_row = result[result["id"] == "bowtie"].iloc[0]
        assert bowtie_row["geom_was_repaired"] == True  # noqa: E712
        assert bowtie_row["geom_repair_method"] == "make_valid"

    def test_multipart_detected(self, sample_geom_gdf):
        result = preprocess_geometry(sample_geom_gdf)
        multi_row = result[result["id"] == "multi"].iloc[0]
        assert multi_row["geom_is_multipart"] == True  # noqa: E712
        assert multi_row["geom_component_count"] == 2

    def test_holes_detected(self, sample_geom_gdf):
        result = preprocess_geometry(sample_geom_gdf)
        holed_row = result[result["id"] == "holed"].iloc[0]
        assert holed_row["geom_has_holes"] == True  # noqa: E712
        assert holed_row["geom_hole_count"] == 1

    def test_implausible_flagged_not_deleted(self, sample_geom_gdf):
        result = preprocess_geometry(sample_geom_gdf)
        tiny_row = result[result["id"] == "tiny"].iloc[0]
        assert tiny_row["geom_is_implausible"] == True  # noqa: E712
        assert "area_too_small" in str(tiny_row["geom_implausible_reason"])
        # Record NOT deleted
        assert len(result) == len(sample_geom_gdf)


class TestVerticalDataModes:
    def test_observed_only(self, sample_vertical_gdf):
        result = compute_vertical_data(sample_vertical_gdf, VerticalDataMode.OBSERVED_ONLY)
        # First row has floors=4, no height
        assert result.iloc[0]["storeys_final"] == 4
        assert result.iloc[0]["storeys_source"] == HeightSource.OBSERVED_FLOORS.value
        # Second row has height=15, no floors — should NOT derive in observed_only
        assert pd.isna(result.iloc[1]["storeys_final"])
        assert result.iloc[1]["storeys_source"] == HeightSource.MISSING.value

    def test_observed_plus_derived(self, sample_vertical_gdf):
        result = compute_vertical_data(sample_vertical_gdf, VerticalDataMode.OBSERVED_PLUS_DERIVED)
        # Second row: height=15, no floors → derived storeys = round(15/3.0) = 5
        assert result.iloc[1]["storeys_final"] == 5
        assert result.iloc[1]["storeys_source"] == HeightSource.DERIVED_FROM_HEIGHT.value
        # First row: floors=4, no height → derived height = 3.5 + 3*3.0 = 12.5
        assert result.iloc[0]["height_final_m"] == pytest.approx(12.5)
        assert result.iloc[0]["height_source"] == HeightSource.DERIVED_FROM_FLOORS.value

    def test_all_classified_retains_missing(self, sample_vertical_gdf):
        result = compute_vertical_data(sample_vertical_gdf, VerticalDataMode.ALL_CLASSIFIED)
        # Third row: no floors, no height → missing but record retained
        assert pd.isna(result.iloc[2]["storeys_final"])
        assert result.iloc[2]["storeys_source"] == HeightSource.MISSING.value
        assert result.iloc[2]["vertical_data_available"] == False  # noqa: E712
        # Record not excluded
        assert len(result) == 5

    def test_no_universal_imputation(self, sample_vertical_gdf):
        """Verify no mode silently applies a universal storey count."""
        for mode in VerticalDataMode:
            result = compute_vertical_data(sample_vertical_gdf, mode)
            # Row 2 has no floors and no height — must stay missing in all modes
            assert pd.isna(result.iloc[2]["storeys_final"])

    def test_gfa_calculated_when_storeys_available(self, sample_vertical_gdf):
        result = compute_vertical_data(sample_vertical_gdf, VerticalDataMode.OBSERVED_ONLY)
        # First row: floors=4, area=500 → GFA = 2000
        assert result.iloc[0]["gfa_est_m2"] == pytest.approx(2000.0)
        assert "observed_floors" in result.iloc[0]["gfa_method"]

    def test_gfa_missing_without_storeys(self, sample_vertical_gdf):
        result = compute_vertical_data(sample_vertical_gdf, VerticalDataMode.OBSERVED_ONLY)
        # Third row: no floors, no height → no GFA
        assert np.isnan(result.iloc[2]["gfa_est_m2"])
