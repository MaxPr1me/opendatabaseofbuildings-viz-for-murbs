"""Tests for the full-population multi-pathway pipeline."""

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box

from murb_geometry.pipeline import (
    PRECISION_LEVELS,
    TIERED_LEVELS,
    _parse_int,
    _parse_numeric,
    classify_dataframe,
    compute_metrics_vectorized,
    filter_pathway,
)


@pytest.fixture
def sample_gdf():
    """Create a small GeoDataFrame mimicking ODB structure."""
    data = {
        "type": [
            "Apartment",  # apartment + storeys/units -> confirmed
            "Residential",  # residential context + large footprint -> possible
            "Commercial",  # non_murb
            "MultiFamily",  # multi_residential + storeys/units -> confirmed
            None,  # no type, tiny footprint -> non_murb
            "Single Family Dwelling",  # residential_single -> non_murb
            "Apartment",  # apartment + storeys/units -> confirmed
        ],
        "units": ["12", "1", "..", "8", "..", "1", "50"],
        "floors": ["4", "2", "3", "6", "..", "1", "15"],
        "height": ["..", "..", "..", "18.0", "..", "..", "45.0"],
        "geometry": [
            box(0, 0, 30, 20),  # 600 m² apartment
            box(0, 0, 30, 25),  # 750 m² residential (large footprint)
            box(0, 0, 50, 30),  # 1500 m² commercial
            box(0, 0, 25, 25),  # 625 m² multi-residential
            box(0, 0, 5, 5),  # 25 m² (too small)
            box(0, 0, 8, 8),  # 64 m² single-family
            box(0, 0, 40, 25),  # 1000 m² large apartment
        ],
    }
    return gpd.GeoDataFrame(data, geometry="geometry", crs="EPSG:3347")


class TestParseNumeric:
    def test_valid_float(self):
        assert _parse_numeric("12.5") == 12.5

    def test_valid_int_as_float(self):
        assert _parse_numeric("4") == 4.0

    def test_missing_marker(self):
        assert _parse_numeric("..") is None

    def test_empty_string(self):
        assert _parse_numeric("") is None

    def test_none(self):
        assert _parse_numeric(None) is None

    def test_invalid(self):
        assert _parse_numeric("abc") is None

    def test_na(self):
        assert _parse_numeric("NA") is None


class TestParseInt:
    def test_valid(self):
        assert _parse_int("4") == 4

    def test_float_input(self):
        assert _parse_int("4.5") == 4

    def test_missing(self):
        assert _parse_int("..") is None


class TestClassifyDataframe:
    def test_all_records_classified(self, sample_gdf):
        result = classify_dataframe(sample_gdf)
        assert len(result) == len(sample_gdf)
        assert "confidence_level" in result.columns
        assert "rule_id" in result.columns
        assert result["confidence_level"].notna().all()

    def test_apartment_classified_confirmed(self, sample_gdf):
        result = classify_dataframe(sample_gdf)
        # First row: "Apartment" + floors=4/units=12 -> confirmed_murb (storey/unit verified)
        assert result.iloc[0]["confidence_level"] == "confirmed_murb"

    def test_multi_residential_classified(self, sample_gdf):
        result = classify_dataframe(sample_gdf)
        # Fourth row: "MultiFamily" + floors=6/units=8 -> confirmed_murb (storey/unit verified)
        assert result.iloc[3]["confidence_level"] == "confirmed_murb"

    def test_commercial_classified_non_murb(self, sample_gdf):
        result = classify_dataframe(sample_gdf)
        # Third row: "Commercial" → non_murb
        assert result.iloc[2]["confidence_level"] == "non_murb"

    def test_no_row_caps(self, sample_gdf):
        """Verify no arbitrary row limits are applied."""
        # Create a larger dataset
        large_gdf = pd.concat([sample_gdf] * 100, ignore_index=True)
        large_gdf = gpd.GeoDataFrame(large_gdf, geometry="geometry", crs="EPSG:3347")
        result = classify_dataframe(large_gdf)
        assert len(result) == 700  # 7 * 100


class TestFilterPathway:
    def test_precision_pathway(self, sample_gdf):
        classified = classify_dataframe(sample_gdf)
        precision = filter_pathway(classified, "precision")
        # Only confirmed_murb and high_confidence_murb
        assert all(level in PRECISION_LEVELS for level in precision["confidence_level"].unique())

    def test_tiered_pathway(self, sample_gdf):
        classified = classify_dataframe(sample_gdf)
        tiered = filter_pathway(classified, "tiered")
        # All tiered levels
        assert all(level in TIERED_LEVELS for level in tiered["confidence_level"].unique())

    def test_tiered_superset_of_precision(self, sample_gdf):
        classified = classify_dataframe(sample_gdf)
        precision = filter_pathway(classified, "precision")
        tiered = filter_pathway(classified, "tiered")
        assert len(tiered) >= len(precision)

    def test_invalid_pathway_raises(self, sample_gdf):
        classified = classify_dataframe(sample_gdf)
        with pytest.raises(ValueError, match="Unknown pathway"):
            filter_pathway(classified, "invalid")


class TestComputeMetrics:
    def test_metrics_added(self, sample_gdf):
        classified = classify_dataframe(sample_gdf)
        precision = filter_pathway(classified, "precision")
        if precision.empty:
            pytest.skip("No precision buildings in sample")
        result = compute_metrics_vectorized(precision)
        assert "aspect_ratio" in result.columns
        assert "compactness" in result.columns
        assert "rectangularity" in result.columns
        assert "mrr_length_m" in result.columns
        assert "convexity" in result.columns

    def test_metrics_positive(self, sample_gdf):
        classified = classify_dataframe(sample_gdf)
        precision = filter_pathway(classified, "precision")
        if precision.empty:
            pytest.skip("No precision buildings in sample")
        result = compute_metrics_vectorized(precision)
        assert (result["aspect_ratio"] >= 1.0).all()
        assert (result["compactness"] > 0).all()
        assert (result["compactness"] <= 1.0).all()

    def test_metrics_match_per_row(self, sample_gdf):
        """Vectorized frame metrics match the per-row reference implementation."""
        from murb_geometry.geometry.metrics import compute_geometry_metrics

        classified = classify_dataframe(sample_gdf)
        tiered = filter_pathway(classified, "tiered")
        if tiered.empty:
            pytest.skip("No tiered buildings in sample")
        result = compute_metrics_vectorized(tiered)
        keys = [
            "perimeter_m",
            "compactness",
            "convexity",
            "rectangularity",
            "mrr_length_m",
            "mrr_width_m",
            "mrr_area_m2",
            "aspect_ratio",
            "orientation_deg",
            "hole_count",
            "hole_area_m2",
            "vertex_count",
        ]
        for _, row in result.iterrows():
            expected = compute_geometry_metrics(row.geometry)
            for key in keys:
                assert row[key] == pytest.approx(expected[key], rel=1e-9, abs=1e-9)
