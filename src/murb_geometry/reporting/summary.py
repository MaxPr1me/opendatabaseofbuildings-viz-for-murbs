"""Run coverage and data-quality reports derived from the pipeline manifest.

Consumes the persisted run manifest only (no re-derivation) and produces a
per-province coverage table that makes the classification coverage bias explicit:
how many records each province contributes to each pathway, and which confidence
tier dominates. This is distinct from the RQ1-RQ10 research report.
"""

from __future__ import annotations

import csv
import json
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)

POSITIVE_TIERS = ["confirmed_murb", "high_confidence_murb", "probable_murb", "possible_murb"]


def build_coverage_table(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Build a per-province coverage table from the run manifest."""
    prov = manifest["stages"]["province_processing"]
    table: list[dict[str, Any]] = []
    for name, data in sorted(prov.items()):
        total = data.get("total_records", 0)
        tiered = data.get("tiered_count", 0)
        precision = data.get("precision_count", 0)
        cls = data.get("classification_summary", {})
        dominant = ""
        if tiered:
            best = max(POSITIVE_TIERS, key=lambda t: cls.get(t, 0))
            if cls.get(best, 0) > 0:
                dominant = best
        table.append(
            {
                "province": name,
                "total_records": total,
                "precision_murbs": precision,
                "tiered_murbs": tiered,
                "pct_tiered": round(100.0 * tiered / total, 4) if total else 0.0,
                "dominant_positive_tier": dominant,
                "confirmed": cls.get("confirmed_murb", 0),
                "high_confidence": cls.get("high_confidence_murb", 0),
                "probable": cls.get("probable_murb", 0),
                "possible": cls.get("possible_murb", 0),
            }
        )
    return table


def write_coverage_report(manifest: dict[str, Any], output_dir: Path) -> Path:
    """Write the per-province coverage table to CSV. Returns the path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    table = build_coverage_table(manifest)
    path = output_dir / "coverage_report.csv"
    if table:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(table[0].keys()))
            writer.writeheader()
            writer.writerows(table)
    logger.info("Coverage report: %s (%d provinces)", path, len(table))
    return path


def write_coverage_report_from_manifest(manifest_path: Path, output_dir: Path) -> Path:
    """Read a manifest from disk and write the coverage report."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return write_coverage_report(manifest, output_dir)
