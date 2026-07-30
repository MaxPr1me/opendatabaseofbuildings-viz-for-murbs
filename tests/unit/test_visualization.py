"""Tests for the visualization charts module."""

import plotly.graph_objects as go

from murb_geometry.visualization import charts


def _manifest() -> dict:
    return {
        "stages": {
            "province_processing": {
                "NS": {
                    "precision_count": 2671,
                    "tiered_count": 2888,
                    "classification_summary": {
                        "confirmed_murb": 189,
                        "high_confidence_murb": 2482,
                        "possible_murb": 217,
                    },
                },
                "QC": {
                    "precision_count": 0,
                    "tiered_count": 2549,
                    "classification_summary": {"possible_murb": 2549},
                },
            }
        }
    }


def test_counts_by_province_returns_figure() -> None:
    fig = charts.counts_by_province(_manifest())
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0


def test_classification_by_province_returns_figure() -> None:
    fig = charts.classification_by_province(_manifest())
    assert isinstance(fig, go.Figure)


def test_metric_distribution_by_confidence() -> None:
    import pandas as pd

    df = pd.DataFrame(
        {
            "confidence_level": ["confirmed_murb", "possible_murb", "confirmed_murb"],
            "footprint_area_m2": [600.0, 800.0, 720.0],
        }
    )
    fig = charts.metric_distribution_by_confidence(
        df, "footprint_area_m2", "Area", "Area (m2)"
    )
    assert isinstance(fig, go.Figure)
