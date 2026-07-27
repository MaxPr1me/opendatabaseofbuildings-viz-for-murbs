"""Classify NS buildings and produce MURB-focused outputs.

Nova Scotia has the richest unit-count data in Canada (23% coverage,
121K buildings with units). This script targets buildings with
units >= 4 to characterize actual MURBs.
"""

import json
from pathlib import Path

import geopandas as gpd
import numpy as np

from murb_geometry.classification.classifier import classify_building, normalize_type_value
from murb_geometry.geometry.metrics import compute_geometry_metrics
from murb_geometry.statistics.descriptive import compute_descriptive_stats

# Load buildings with unit counts >= 4 (actual MURBs)
print("Loading NS buildings with units >= 4 (SQL filter)...")
gdf = gpd.read_file(
    "data/ODB_v3_NS/ODB_v3_NS.gpkg",
    where="units != '..' AND CAST(units AS INTEGER) >= 4",
    rows=2000,
)
print(f"Loaded {len(gdf)} MURB candidates from Nova Scotia")

# Compute metrics and classify
murb_areas: list[float] = []
murb_aspect: list[float] = []
murb_compact: list[float] = []
murb_rect: list[float] = []
murb_orient: list[float] = []
murb_units: list[float] = []
murb_floors: list[float] = []
classification_counts: dict[str, int] = {}

for _, row in gdf.iterrows():
    m = compute_geometry_metrics(row.geometry)
    type_norm = normalize_type_value(row.get("type"))
    units_str = row.get("units")
    units_num = int(float(units_str)) if units_str and units_str != ".." else None
    floors_str = row.get("floors")
    floors_num = int(float(floors_str)) if floors_str and floors_str != ".." else None

    result = classify_building(
        type_normalized=type_norm,
        units_numeric=units_num,
        floors_numeric=floors_num,
        footprint_area_m2=m["footprint_area_m2"],
    )
    classification_counts[result.confidence_level] = (
        classification_counts.get(result.confidence_level, 0) + 1
    )

    murb_areas.append(m["footprint_area_m2"])
    murb_aspect.append(m["aspect_ratio"])
    murb_compact.append(m["compactness"])
    murb_rect.append(m["rectangularity"])
    murb_orient.append(m["orientation_deg"])
    if units_num:
        murb_units.append(float(units_num))
    if floors_num:
        murb_floors.append(float(floors_num))

# Print results
print(f"\nClassification (n={len(gdf)}):")
for level, count in sorted(classification_counts.items(), key=lambda x: -x[1]):
    print(f"  {level}: {count} ({100*count/len(gdf):.1f}%)")

print(f"\n--- MURB Geometry Statistics (n={len(murb_areas)}) ---")
area_stats = compute_descriptive_stats(murb_areas, "footprint_area_m2")
print(f"\nFootprint Area (m2):")
print(f"  min={area_stats['min']:.0f}, P25={area_stats['p25']:.0f}, "
      f"median={area_stats['median']:.0f}, P75={area_stats['p75']:.0f}, "
      f"max={area_stats['max']:.0f}")
print(f"  mean={area_stats['mean']:.0f}, std={area_stats['std']:.0f}")

ar_stats = compute_descriptive_stats(murb_aspect, "aspect_ratio")
print(f"\nAspect Ratio:")
print(f"  P25={ar_stats['p25']:.2f}, median={ar_stats['median']:.2f}, "
      f"P75={ar_stats['p75']:.2f}, max={ar_stats['max']:.2f}")

if murb_units:
    unit_stats = compute_descriptive_stats(murb_units, "units")
    print(f"\nDwelling Units:")
    print(f"  P25={unit_stats['p25']:.0f}, median={unit_stats['median']:.0f}, "
          f"P75={unit_stats['p75']:.0f}, max={unit_stats['max']:.0f}")

if murb_floors:
    floor_stats = compute_descriptive_stats(murb_floors, "floors")
    print(f"\nStoreys:")
    print(f"  P25={floor_stats['p25']:.0f}, median={floor_stats['median']:.0f}, "
          f"P75={floor_stats['p75']:.0f}, max={floor_stats['max']:.0f}")

# Save results
Path("outputs/reports").mkdir(parents=True, exist_ok=True)
output = {
    "province": "NS",
    "description": "Nova Scotia MURB geometry characterization",
    "filter": "units >= 4",
    "sample_size": len(gdf),
    "classification": classification_counts,
    "geometry_statistics": {
        "footprint_area_m2": compute_descriptive_stats(murb_areas, "footprint_area_m2"),
        "aspect_ratio": compute_descriptive_stats(murb_aspect, "aspect_ratio"),
        "compactness": compute_descriptive_stats(murb_compact, "compactness"),
        "rectangularity": compute_descriptive_stats(murb_rect, "rectangularity"),
        "orientation_deg": compute_descriptive_stats(murb_orient, "orientation_deg"),
    },
    "attribute_statistics": {},
}
if murb_units:
    output["attribute_statistics"]["units"] = compute_descriptive_stats(murb_units, "units")
if murb_floors:
    output["attribute_statistics"]["floors"] = compute_descriptive_stats(murb_floors, "floors")

with open("outputs/reports/ns_murb_analysis.json", "w") as f:
    json.dump(output, f, indent=2, default=str)
print("\nSaved: outputs/reports/ns_murb_analysis.json")
