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


class TestPreprocessGeometryEdgeCases:
    """Additional edge-case tests for geometry preprocessing."""

    def test_empty_geometry_flagged(self):
        from shapely.geometry import Polygon as ShapelyPolygon

        empty = ShapelyPolygon()
        gdf = gpd.GeoDataFrame({"id": ["empty"]}, geometry=[empty], crs="EPSG:3347")
        result = preprocess_geometry(gdf)
        assert result.iloc[0]["geom_is_empty"] == True  # noqa: E712
        assert len(result) == 1  # Not deleted

    def test_large_implausible_flagged(self):
        huge = box(0, 0, 1000, 200)  # 200,000 m² — too large
        gdf = gpd.GeoDataFrame({"id": ["huge"]}, geometry=[huge], crs="EPSG:3347")
        result = preprocess_geometry(gdf)
        assert result.iloc[0]["geom_is_implausible"] == True  # noqa: E712
        assert "area_too_large" in str(result.iloc[0]["geom_implausible_reason"])

    def test_area_delta_after_repair(self):
        # Bowtie polygon — self-intersecting, original area is 0
        bowtie = Polygon([(0, 0), (10, 10), (10, 0), (0, 10), (0, 0)])
        gdf = gpd.GeoDataFrame({"id": ["bt"]}, geometry=[bowtie], crs="EPSG:3347")
        result = preprocess_geometry(gdf)
        assert result.iloc[0]["geom_was_repaired"] == True  # noqa: E712
        # Repaired geometry has positive area (two triangles)
        assert result.iloc[0]["geom_repaired_area_m2"] > 0

    def test_normal_polygon_not_implausible(self):
        normal = box(0, 0, 20, 30)  # 600 m² — normal size
        gdf = gpd.GeoDataFrame({"id": ["norm"]}, geometry=[normal], crs="EPSG:3347")
        result = preprocess_geometry(gdf)
        assert result.iloc[0]["geom_is_implausible"] == False  # noqa: E712
        assert result.iloc[0]["geom_is_valid"] == True  # noqa: E712

    def test_row_count_reconciliation(self):
        """Input and output always have same row count."""
        geoms = [box(0, 0, 10, 10)] * 50 + [None] * 5
        gdf = gpd.GeoDataFrame({"id": list(range(55))}, geometry=geoms, crs="EPSG:3347")
        result = preprocess_geometry(gdf)
        assert len(result) == 55

    def test_multipolygon_hole_count(self):
        """MultiPolygon holes summed across components."""
        outer1 = box(0, 0, 20, 20)
        hole1 = box(5, 5, 15, 15)
        p1 = Polygon(outer1.exterior.coords, [hole1.exterior.coords])
        outer2 = box(30, 0, 50, 20)
        hole2 = box(35, 5, 45, 15)
        p2 = Polygon(outer2.exterior.coords, [hole2.exterior.coords])
        multi = MultiPolygon([p1, p2])
        gdf = gpd.GeoDataFrame({"id": ["mh"]}, geometry=[multi], crs="EPSG:3347")
        result = preprocess_geometry(gdf)
        assert result.iloc[0]["geom_hole_count"] == 2
        assert result.iloc[0]["geom_is_multipart"] == True  # noqa: E712


class TestVerticalDataEdgeCases:
    """Additional vertical-data mode tests."""

    def test_both_floors_and_height_observed(self):
        """When both are available, both are used as observed."""
        gdf = gpd.GeoDataFrame(
            {
                "floors_numeric": [8],
                "height_numeric": [24.0],
                "footprint_area_m2": [1000.0],
                "geometry": [box(0, 0, 40, 25)],
            },
            crs="EPSG:3347",
        )
        result = compute_vertical_data(gdf, VerticalDataMode.OBSERVED_ONLY)
        assert result.iloc[0]["storeys_final"] == 8
        assert result.iloc[0]["height_final_m"] == 24.0
        assert result.iloc[0]["storeys_source"] == HeightSource.OBSERVED_FLOORS.value
        assert result.iloc[0]["height_source"] == HeightSource.OBSERVED_HEIGHT.value

    def test_derived_storeys_from_tall_building(self):
        """Tall building height → correct derived storeys."""
        gdf = gpd.GeoDataFrame(
            {
                "floors_numeric": [None],
                "height_numeric": [45.0],
                "footprint_area_m2": [800.0],
                "geometry": [box(0, 0, 40, 20)],
            },
            crs="EPSG:3347",
        )
        result = compute_vertical_data(gdf, VerticalDataMode.OBSERVED_PLUS_DERIVED)
        # 45 / 3.0 = 15 storeys
        assert result.iloc[0]["storeys_final"] == 15
        assert result.iloc[0]["storeys_source"] == HeightSource.DERIVED_FROM_HEIGHT.value

    def test_gfa_uses_correct_storeys_source(self):
        """GFA method field references the correct source."""
        gdf = gpd.GeoDataFrame(
            {
                "floors_numeric": [None],
                "height_numeric": [12.0],
                "footprint_area_m2": [500.0],
                "geometry": [box(0, 0, 25, 20)],
            },
            crs="EPSG:3347",
        )
        result = compute_vertical_data(gdf, VerticalDataMode.OBSERVED_PLUS_DERIVED)
        # 12/3.0 = 4 storeys, GFA = 500*4 = 2000
        assert result.iloc[0]["gfa_est_m2"] == pytest.approx(2000.0)
        assert "derived_from_height" in result.iloc[0]["gfa_method"]
