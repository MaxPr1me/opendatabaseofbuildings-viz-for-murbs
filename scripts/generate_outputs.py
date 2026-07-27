"""Generate sample outputs for the repository.

Processes small provinces (NT, YT, PE) to produce committed output
files that demonstrate the pipeline without requiring the full
national dataset.
"""

import json
from pathlib import Path

import geopandas as gpd

from murb_geometry.classification.classifier import classify_building, normalize_type_value
from murb_geometry.excel.workbook import create_summary_workbook
from murb_geometry.geometry.metrics import compute_geometry_metrics
from murb_geometry.ingestion.inventory import discover_geopackages, run_inventory
from murb_geometry.statistics.descriptive import compute_descriptive_stats

# --- Configuration ---
DATA_DIR = Path("data")
OUTPUT_DIR = Path("outputs")
SAMPLE_PROVINCES = ["NT", "YT", "PE", "NL"]  # Small files for fast processing
SAMPLE_ROWS = 1000  # rows per file for metrics

print("=" * 60)
print("Canadian MURB Geometry Analysis — Sample Output Generation")
print("=" * 60)

# --- Step 1: Inventory (small files only for speed) ---
print("\n[1/5] Running inventory on sample provinces...")
from murb_geometry.ingestion.inventory import inspect_geopackage

inventory_items = []
for gpkg_path in discover_geopackages(DATA_DIR):
    prov = gpkg_path.stem.replace("ODB_v3_", "").split("_")[0]
    if prov not in SAMPLE_PROVINCES:
        continue
    print(f"  Inspecting: {gpkg_path.name}...")
    item = inspect_geopackage(gpkg_path, compute_hash=False)
    inventory_items.append(item)

# Build report manually for the subset
from murb_geometry import __version__
from datetime import datetime, UTC

(OUTPUT_DIR / "reports").mkdir(parents=True, exist_ok=True)
inventory_report = {
    "generated_at": datetime.now(UTC).isoformat(),
    "software_version": __version__,
    "data_directory": str(DATA_DIR),
    "total_files": len(inventory_items),
    "total_records": sum(i.total_records for i in inventory_items),
    "total_size_mb": round(sum(i.file_size_mb for i in inventory_items), 1),
    "files": [i.model_dump() for i in inventory_items],
}
with open(OUTPUT_DIR / "reports" / "inventory.json", "w") as f:
    json.dump(inventory_report, f, indent=2)
print(f"  {len(inventory_items)} files, {inventory_report['total_records']:,} records")

# --- Step 2: Geometry metrics on sample provinces ---
print("\n[2/5] Computing geometry metrics (sampled)...")
all_metrics: list[dict] = []
areas: list[float] = []
aspect_ratios: list[float] = []
compactness_vals: list[float] = []
rectangularity_vals: list[float] = []

for gpkg_path in discover_geopackages(DATA_DIR):
    prov = gpkg_path.stem.replace("ODB_v3_", "").split("_")[0]
    if prov not in SAMPLE_PROVINCES:
        continue
    print(f"  Processing: {gpkg_path.name}...")
    gdf = gpd.read_file(gpkg_path, rows=SAMPLE_ROWS)
    for _, row in gdf.iterrows():
        geom = row.geometry
        m = compute_geometry_metrics(geom)
        m["province"] = prov
        m["source"] = row.get("source", "")
        all_metrics.append(m)
        areas.append(m["footprint_area_m2"])
        aspect_ratios.append(m["aspect_ratio"])
        compactness_vals.append(m["compactness"])
        rectangularity_vals.append(m["rectangularity"])

print(f"  Total buildings measured: {len(all_metrics)}")

# --- Step 3: Classification on sample provinces ---
print("\n[3/5] Running MURB classification (sampled)...")
classification_summary: dict[str, dict[str, int]] = {}

for gpkg_path in discover_geopackages(DATA_DIR):
    prov = gpkg_path.stem.replace("ODB_v3_", "").split("_")[0]
    if prov not in SAMPLE_PROVINCES:
        continue
    gdf = gpd.read_file(gpkg_path, rows=SAMPLE_ROWS)
    prov_results: dict[str, int] = {}
    for _, row in gdf.iterrows():
        type_norm = normalize_type_value(row.get("type"))
        units_str = row.get("units")
        units_num = int(units_str) if units_str and units_str != ".." else None
        floors_str = row.get("floors")
        floors_num = int(floors_str) if floors_str and floors_str != ".." else None
        area = compute_geometry_metrics(row.geometry)["footprint_area_m2"]
        result = classify_building(
            type_normalized=type_norm,
            units_numeric=units_num,
            floors_numeric=floors_num,
            footprint_area_m2=area,
        )
        prov_results[result.confidence_level] = prov_results.get(result.confidence_level, 0) + 1
    classification_summary[prov] = prov_results
    print(f"  {prov}: {dict(sorted(prov_results.items(), key=lambda x: -x[1]))}")

# --- Step 4: Summary statistics ---
print("\n[4/5] Computing summary statistics...")
summary_stats = [
    compute_descriptive_stats(areas, "footprint_area_m2"),
    compute_descriptive_stats(aspect_ratios, "aspect_ratio"),
    compute_descriptive_stats(compactness_vals, "compactness"),
    compute_descriptive_stats(rectangularity_vals, "rectangularity"),
]

# Save summary
(OUTPUT_DIR / "reports").mkdir(parents=True, exist_ok=True)
with open(OUTPUT_DIR / "reports" / "summary_stats.json", "w") as f:
    json.dump(summary_stats, f, indent=2, default=str)

# Save classification results
with open(OUTPUT_DIR / "reports" / "classification_summary.json", "w") as f:
    json.dump(classification_summary, f, indent=2)

print("  Summary statistics saved to: outputs/reports/summary_stats.json")
print("  Classification saved to: outputs/reports/classification_summary.json")

# --- Step 5: Excel report ---
print("\n[5/5] Generating Excel report...")
inv = json.loads((OUTPUT_DIR / "reports" / "inventory.json").read_text())
completeness_data = []
for fi in inv["files"]:
    row: dict[str, object] = {
        "province": fi["province_territory"],
        "records": fi["total_records"],
        "size_mb": fi["file_size_mb"],
    }
    for fc in fi["field_completeness"]:
        row[fc["field_name"] + "_pct"] = fc["completeness_pct"]
    completeness_data.append(row)

(OUTPUT_DIR / "excel").mkdir(parents=True, exist_ok=True)
create_summary_workbook(
    OUTPUT_DIR / "excel" / "murb_national_summary.xlsx",
    completeness_data=completeness_data,
    summary_stats=summary_stats,
    metadata={
        "Source": "Statistics Canada Open Database of Buildings v3",
        "Scope": "National inventory + sampled geometry metrics",
        "Sample provinces (metrics)": ", ".join(SAMPLE_PROVINCES),
        "Sample size per file": str(SAMPLE_ROWS),
        "Total buildings measured": str(len(all_metrics)),
    },
)
print("  Excel report saved to: outputs/excel/murb_national_summary.xlsx")

print("\n" + "=" * 60)
print("Complete! All outputs in: outputs/")
print("=" * 60)
