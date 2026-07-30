"""Tests for the reporting coverage summary."""

from murb_geometry.reporting.summary import build_coverage_table


def _manifest() -> dict:
    return {
        "stages": {
            "province_processing": {
                "NS": {
                    "total_records": 528307,
                    "precision_count": 2671,
                    "tiered_count": 2888,
                    "classification_summary": {
                        "confirmed_murb": 189,
                        "high_confidence_murb": 2482,
                        "possible_murb": 217,
                    },
                },
                "MB": {
                    "total_records": 656775,
                    "precision_count": 0,
                    "tiered_count": 0,
                    "classification_summary": {},
                },
            }
        }
    }


def test_build_coverage_table() -> None:
    table = build_coverage_table(_manifest())
    assert len(table) == 2

    ns = next(r for r in table if r["province"] == "NS")
    assert ns["tiered_murbs"] == 2888
    assert ns["precision_murbs"] == 2671
    assert ns["dominant_positive_tier"] == "high_confidence_murb"
    assert ns["pct_tiered"] > 0

    mb = next(r for r in table if r["province"] == "MB")
    assert mb["tiered_murbs"] == 0
    assert mb["dominant_positive_tier"] == ""
