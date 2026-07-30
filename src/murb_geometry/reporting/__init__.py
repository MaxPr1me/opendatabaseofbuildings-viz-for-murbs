"""Reporting module — data-quality reports and run manifests."""

from murb_geometry.reporting.summary import (
    build_coverage_table,
    write_coverage_report,
    write_coverage_report_from_manifest,
)

__all__ = [
    "build_coverage_table",
    "write_coverage_report",
    "write_coverage_report_from_manifest",
]
