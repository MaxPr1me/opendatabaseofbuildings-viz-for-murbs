"""National full-population run — all provinces, multi-pathway (Option C).

This script replaces scripts/complete_run.py for production use.
No arbitrary row caps. Full eligible populations processed.
"""
import logging
import json
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)

from murb_geometry.pipeline import run_full_pipeline

if __name__ == "__main__":
    print("=" * 70)
    print("  NATIONAL MURB ANALYSIS — Full Population, Multi-Pathway (Option C)")
    print("  Classification: precision (confirmed+high) and tiered (all positive)")
    print("  Row limits: NONE")
    print("=" * 70)
    print()

    manifest = run_full_pipeline()

    # Print summary
    totals = manifest["stages"]["national_totals"]
    print()
    print("=" * 70)
    print("  NATIONAL RESULTS")
    print("=" * 70)
    print(f"  Precision pathway: {totals['precision_buildings']:,} buildings")
    print(f"  Tiered pathway:    {totals['tiered_buildings']:,} buildings")
    print()
    print("  Per-Province Breakdown:")
    for prov, data in manifest["stages"]["province_processing"].items():
        print(
            f"    {prov:>2}: {data['total_records']:>10,} total | "
            f"{data['precision_count']:>6,} precision | "
            f"{data['tiered_count']:>6,} tiered | "
            f"{data['timing_seconds']:.1f}s"
        )
    print()
    print("  Outputs:")
    print("    data/processed/murbs_precision.parquet")
    print("    data/processed/murbs_tiered.parquet")
    print("    outputs/reports/run_manifest.json")
    print("    outputs/reports/classification_summary.csv")
    print("    outputs/reports/pathway_sensitivity.csv")
    print("=" * 70)
