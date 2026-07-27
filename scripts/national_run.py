"""National production run — process ALL provinces.

Runs the complete pipeline across all 15 GeoPackage files (~14.4M records).
Produces inventory, geometry metrics, classification, and Excel report.

NOTE: The inventory step (field completeness queries) is the bottleneck.
On the full dataset this takes 30-60+ minutes due to full table scans
on multi-GB GeoPackage files without SQLite indexes.
"""

import json
import time
from datetime import datetime, UTC
from pathlib import Path

import geopandas as gpd
import numpy as np

from murb_geometry.archetypes.clustering import cluster_buildings
from murb_geometry.classification.classifier import classify_building, normalize_type_value
from murb_geometry.excel.workbook import create_summary_workbook
from murb_geometry.geometry.metrics import compute_geometry_metrics
from murb_geometry.ingestion.inventory import discover_geopackages, inspect_geopackage
from murb_geometry.statistics.descriptive import compute_descriptive_stats

# --- Configuration ---
DATA_DIR = Path("data")
OUTPUT_DIR = Path("outputs")
METRICS_SAMPLE_PER_FILE = 500  # rows to sample for geometry metrics
CLASSIFY_SAMPLE_PER_FILE = 500  # rows to sample for classification

start_time = time.time()

print("=" * 70)
print("  Canadian MURB Geometry Analysis — NATIONAL PRODUCTION RUN")
print(f"  Started: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}")
print("=" * 70)

# --- Step 1: National Inventory ---
print("\n[1/5] National GeoPackage Inventory")
print("-" * 50)

gpkg_files = discover_geopackages(DATA_DIR)
print(f"  Found {len(gpkg_files)} GeoPackage files")

inventory_items = []
for i, gpkg_path in enumerate(gpkg_files, 1):
    print(f"  [{i}/{len(gpkg_files)}] {gpkg_path.name}...", end=" ", flush=True)
    t0 = time.time()
    item = inspect_geopackage(gpkg_path, compute_hash=False)
    elapsed = time.time() - t0
    print(f"{item.total_records:>10,} records ({elapsed:.1f}s)")
    inventory_items.append(item)

# Save inventory
(OUTPUT_DIR / "reports").mkdir(parents=True, exist_ok=True)
from murb_geometry import __version__

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

total_records = inventory_report["total_records"]
print(f"\n  TOTAL: {total_records:,} records, {inventory_report['total_size_mb']:.0f} MB")
print(f"  Saved: outputs/reports/inventory.json")

# --- Step 2: Geometry Metrics (sampled) ---
print(f"\n[2/5] Geometry Metrics (sample={METRICS_SAMPLE_PER_FILE}/file)")
print("-" * 50)

all_areas: list[float] = []
all_aspect: list[float] = []
all_compact: list[float] = []
all_rect: list[float] = []
province_metrics: dict[str, list[float]] = {}

for gpkg_path in gpkg_files:
    prov = gpkg_path.stem.replace("ODB_v3_", "")
    print(f"  {prov}...", end=" ", flush=True)
    gdf = gpd.read_file(gpkg_path, rows=METRICS_SAMPLE_PER_FILE)
    prov_areas: list[float] = []
    for geom in gdf.geometry:
        m = compute_geometry_metrics(geom)
        all_areas.append(m["footprint_area_m2"])
        all_aspect.append(m["aspect_ratio"])
        all_compact.append(m["compactness"])
        all_rect.append(m["rectangularity"])
        prov_areas.append(m["footprint_area_m2"])
    province_metrics[prov] = prov_areas
    stats = compute_descriptive_stats(prov_areas, "area")
    print(f"n={len(prov_areas)}, median={stats['median']:.0f} m²")

# National summary
national_stats = {
    "description": "National geometry metrics (sampled)",
    "sample_per_file": METRICS_SAMPLE_PER_FILE,
    "total_sampled": len(all_areas),
    "footprint_area_m2": compute_descriptive_stats(all_areas, "footprint_area_m2"),
    "aspect_ratio": compute_descriptive_stats(all_aspect, "aspect_ratio"),
    "compactness": compute_descriptive_stats(all_compact, "compactness"),
    "rectangularity": compute_descriptive_stats(all_rect, "rectangularity"),
    "by_province": {
        prov: compute_descriptive_stats(areas, "footprint_area_m2")
        for prov, areas in province_metrics.items()
    },
}
with open(OUTPUT_DIR / "reports" / "summary_stats.json", "w") as f:
    json.dump(national_stats, f, indent=2, default=str)
print(f"\n  National median area: {national_stats['footprint_area_m2']['median']:.0f} m²")

# --- Step 3: Classification (sampled) ---
print(f"\n[3/5] MURB Classification (sample={CLASSIFY_SAMPLE_PER_FILE}/file)")
print("-" * 50)

national_classification: dict[str, int] = {}
province_classification: dict[str, dict[str, int]] = {}

for gpkg_path in gpkg_files:
    prov = gpkg_path.stem.replace("ODB_v3_", "")
    print(f"  {prov}...", end=" ", flush=True)
    gdf = gpd.read_file(gpkg_path, rows=CLASSIFY_SAMPLE_PER_FILE)
    prov_results: dict[str, int] = {}
    for _, row in gdf.iterrows():
        type_norm = normalize_type_value(row.get("type"))
        units_str = row.get("units")
        units_num = None
        if units_str and units_str != "..":
            try:
                units_num = int(float(units_str))
            except (ValueError, TypeError):
                pass
        floors_str = row.get("floors")
        floors_num = None
        if floors_str and floors_str != "..":
            try:
                floors_num = int(float(floors_str))
            except (ValueError, TypeError):
                pass
        m = compute_geometry_metrics(row.geometry)
        result = classify_building(
            type_normalized=type_norm,
            units_numeric=units_num,
            floors_numeric=floors_num,
            footprint_area_m2=m["footprint_area_m2"],
        )
        level = result.confidence_level
        prov_results[level] = prov_results.get(level, 0) + 1
        national_classification[level] = national_classification.get(level, 0) + 1

    province_classification[prov] = prov_results
    # Show top result
    top = max(prov_results.items(), key=lambda x: x[1])
    murb_count = sum(
        v for k, v in prov_results.items()
        if k in ("confirmed_murb", "high_confidence_murb", "probable_murb", "possible_murb")
    )
    print(f"MURBs: {murb_count}/{len(gdf)}")

classification_output = {
    "description": "National MURB classification (sampled)",
    "sample_per_file": CLASSIFY_SAMPLE_PER_FILE,
    "national_totals": national_classification,
    "by_province": province_classification,
}
with open(OUTPUT_DIR / "reports" / "classification_summary.json", "w") as f:
    json.dump(classification_output, f, indent=2)

total_murbs = sum(
    v for k, v in national_classification.items()
    if k in ("confirmed_murb", "high_confidence_murb", "probable_murb", "possible_murb")
)
print(f"\n  National MURB candidates: {total_murbs}/{sum(national_classification.values())}")
print(f"  Classification distribution: {dict(sorted(national_classification.items(), key=lambda x: -x[1]))}")

# --- Step 4: NS MURB Deep Analysis (best data) ---
print("\n[4/5] Nova Scotia MURB Deep Analysis (units >= 4)")
print("-" * 50)

gdf_ns = gpd.read_file(
    "data/ODB_v3_NS/ODB_v3_NS.gpkg",
    where="units != '..' AND CAST(units AS INTEGER) >= 4",
    rows=2766,  # all NS MURBs
)
print(f"  Loaded {len(gdf_ns)} confirmed MURBs")

murb_features: list[list[float]] = []
murb_areas_ns: list[float] = []
murb_aspect_ns: list[float] = []
murb_units_ns: list[float] = []

for _, row in gdf_ns.iterrows():
    m = compute_geometry_metrics(row.geometry)
    murb_areas_ns.append(m["footprint_area_m2"])
    murb_aspect_ns.append(m["aspect_ratio"])
    units_val = float(row.get("units", 0) or 0)
    murb_units_ns.append(units_val)
    murb_features.append([m["footprint_area_m2"], m["aspect_ratio"], m["compactness"], m["rectangularity"]])

ns_analysis = {
    "province": "NS",
    "filter": "units >= 4",
    "n_buildings": len(gdf_ns),
    "footprint_area_m2": compute_descriptive_stats(murb_areas_ns, "footprint_area_m2"),
    "aspect_ratio": compute_descriptive_stats(murb_aspect_ns, "aspect_ratio"),
    "units": compute_descriptive_stats(murb_units_ns, "units"),
}
with open(OUTPUT_DIR / "reports" / "ns_murb_analysis.json", "w") as f:
    json.dump(ns_analysis, f, indent=2, default=str)

area_s = ns_analysis["footprint_area_m2"]
print(f"  Footprint: median={area_s['median']:.0f}, IQR={area_s['p25']:.0f}-{area_s['p75']:.0f} m²")
print(f"  Aspect ratio: median={ns_analysis['aspect_ratio']['median']:.2f}")
print(f"  Units: median={ns_analysis['units']['median']:.0f}")

# Cluster into archetypes
print("  Clustering into 6 archetypes...")
features_arr = np.array(murb_features)
cluster_result = cluster_buildings(features_arr, n_clusters=6, random_seed=42)

archetypes = []
for k in range(cluster_result["n_clusters"]):
    mask = cluster_result["labels"] == k
    medoid_idx = cluster_result["medoid_indices"][k]
    cluster_areas = [murb_areas_ns[i] for i in range(len(murb_areas_ns)) if mask[i]]
    archetypes.append({
        "archetype_id": f"NS-A{k+1:02d}",
        "cluster_size": int(np.sum(mask)),
        "medoid_index": medoid_idx,
        "medoid_building_id": gdf_ns.iloc[medoid_idx]["id"],
        "representative_area_m2": round(murb_areas_ns[medoid_idx], 1),
        "representative_aspect_ratio": round(murb_aspect_ns[medoid_idx], 2),
        "cluster_area_stats": compute_descriptive_stats(cluster_areas, "footprint_area_m2"),
    })
    print(f"    {archetypes[-1]['archetype_id']}: n={archetypes[-1]['cluster_size']}, "
          f"area={archetypes[-1]['representative_area_m2']:.0f} m², "
          f"AR={archetypes[-1]['representative_aspect_ratio']:.2f}")

(OUTPUT_DIR / "archetypes").mkdir(parents=True, exist_ok=True)
arch_output = {
    "description": "MURB archetypes from NS (units >= 4)",
    "method": "K-means (k=6) with medoid selection",
    "n_buildings": len(gdf_ns),
    "features": ["footprint_area_m2", "aspect_ratio", "compactness", "rectangularity"],
    "archetypes": archetypes,
}
with open(OUTPUT_DIR / "archetypes" / "ns_archetypes.json", "w") as f:
    json.dump(arch_output, f, indent=2, default=str)

# --- Step 5: Excel Report ---
print("\n[5/5] Generating Excel Report")
print("-" * 50)

inv = json.loads((OUTPUT_DIR / "reports" / "inventory.json").read_text())
completeness_data: list[dict[str, object]] = []
for fi in inv["files"]:
    row: dict[str, object] = {
        "province": fi["province_territory"],
        "records": fi["total_records"],
        "size_mb": fi["file_size_mb"],
        "sources": len(fi["source_organizations"]),
    }
    for fc in fi["field_completeness"]:
        row[fc["field_name"] + "_pct"] = fc["completeness_pct"]
    completeness_data.append(row)

summary_for_excel = [
    national_stats["footprint_area_m2"],
    national_stats["aspect_ratio"],
    national_stats["compactness"],
    national_stats["rectangularity"],
]

(OUTPUT_DIR / "excel").mkdir(parents=True, exist_ok=True)
create_summary_workbook(
    OUTPUT_DIR / "excel" / "murb_national_summary.xlsx",
    completeness_data=completeness_data,
    summary_stats=summary_for_excel,
    metadata={
        "Source": "Statistics Canada Open Database of Buildings v3",
        "Scope": "All provinces and territories",
        "Total records": f"{total_records:,}",
        "Geometry sample per file": str(METRICS_SAMPLE_PER_FILE),
        "Classification sample per file": str(CLASSIFY_SAMPLE_PER_FILE),
        "NS MURB analysis": f"{len(gdf_ns)} buildings with units >= 4",
        "Archetypes": "6 clusters from NS MURBs",
        "Generated": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
    },
)
print("  Saved: outputs/excel/murb_national_summary.xlsx")

# --- Done ---
elapsed_total = time.time() - start_time
print(f"\n{'=' * 70}")
print(f"  NATIONAL RUN COMPLETE")
print(f"  Duration: {elapsed_total/60:.1f} minutes")
print(f"  Records inventoried: {total_records:,}")
print(f"  Buildings measured: {len(all_areas)}")
print(f"  MURB candidates: {total_murbs}")
print(f"  NS MURBs characterized: {len(gdf_ns)}")
print(f"  Archetypes generated: {len(archetypes)}")
print(f"{'=' * 70}")
print(f"\nOutputs:")
print(f"  outputs/reports/inventory.json")
print(f"  outputs/reports/summary_stats.json")
print(f"  outputs/reports/classification_summary.json")
print(f"  outputs/reports/ns_murb_analysis.json")
print(f"  outputs/archetypes/ns_archetypes.json")
print(f"  outputs/excel/murb_national_summary.xlsx")
print(f"  outputs/gbxml/ns_a05_archetype.xml (previously generated)")
