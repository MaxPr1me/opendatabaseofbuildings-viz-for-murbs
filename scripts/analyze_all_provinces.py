"""Complete national analysis — all provinces with attribute data.

Runs MURB classification and geometry metrics on ALL provinces that
have usable attribute data, using SQL-targeted queries to find actual
MURBs rather than random sampling.

Provinces with MURB-identifiable data:
- NS: 23% units (121K records) — BEST
- NB: 8% units (53K), 3.3% height (22K)
- ON_2: 1.7% units (34K), 8.9% floors (178K)
- ON_3: 1.1% units (19K), 5.6% floors (95K)
- BC: 3.2% floors (41K), 26.5% height (346K)
- AB: 38.5% type (513K), 10.6% height (141K)
"""

import json
import time
from datetime import datetime, UTC
from pathlib import Path

import geopandas as gpd
import numpy as np

from murb_geometry.archetypes.clustering import cluster_buildings
from murb_geometry.classification.classifier import classify_building, normalize_type_value
from murb_geometry.geometry.metrics import compute_geometry_metrics
from murb_geometry.statistics.descriptive import compute_descriptive_stats

OUTPUT_DIR = Path("outputs")
(OUTPUT_DIR / "reports").mkdir(parents=True, exist_ok=True)
(OUTPUT_DIR / "archetypes").mkdir(parents=True, exist_ok=True)

start = time.time()
print("=" * 70)
print("  COMPLETE NATIONAL MURB ANALYSIS — ALL PROVINCES")
print(f"  {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}")
print("=" * 70)

# Define targeted queries per province
PROVINCE_QUERIES = {
    "NS": {
        "file": "data/ODB_v3_NS/ODB_v3_NS.gpkg",
        "where": "units != '..' AND CAST(units AS INTEGER) >= 4",
        "description": "Units >= 4",
        "max_rows": 3000,
    },
    "NB": {
        "file": "data/ODB_v3_NB/ODB_v3_NB.gpkg",
        "where": "units != '..' AND CAST(units AS INTEGER) >= 4",
        "description": "Units >= 4",
        "max_rows": 3000,
    },
    "ON_2": {
        "file": "data/ODB_v3_ON_2/ODB_v3_ON_2.gpkg",
        "where": "units != '..' AND CAST(units AS INTEGER) >= 4",
        "description": "Units >= 4",
        "max_rows": 3000,
    },
    "ON_3": {
        "file": "data/ODB_v3_ON_3/ODB_v3_ON_3.gpkg",
        "where": "units != '..' AND CAST(units AS INTEGER) >= 4",
        "description": "Units >= 4",
        "max_rows": 3000,
    },
    "BC_floors": {
        "file": "data/ODB_v3_BC/ODB_v3_BC.gpkg",
        "where": "floors != '..' AND CAST(floors AS INTEGER) >= 4",
        "description": "Floors >= 4 (multi-storey candidates)",
        "max_rows": 3000,
    },
    "AB_type": {
        "file": "data/ODB_v3_AB/ODB_v3_AB.gpkg",
        "where": "type LIKE '%partment%' OR type LIKE '%ulti%' OR type LIKE '%ondo%'",
        "description": "Type contains apartment/multi/condo",
        "max_rows": 3000,
    },
}

all_murb_metrics: list[dict] = []
province_results: dict[str, dict] = {}

for prov_key, config in PROVINCE_QUERIES.items():
    print(f"\n{'─'*50}")
    print(f"  {prov_key}: {config['description']}")
    print(f"  File: {config['file']}")
    t0 = time.time()

    try:
        gdf = gpd.read_file(
            config["file"],
            where=config["where"],
            rows=config["max_rows"],
        )
    except Exception as e:
        print(f"  ERROR: {e}")
        continue

    elapsed = time.time() - t0
    print(f"  Loaded {len(gdf)} records ({elapsed:.1f}s)")

    if len(gdf) == 0:
        print("  No records matched query — skipping")
        continue

    # Compute metrics
    areas: list[float] = []
    aspects: list[float] = []
    compacts: list[float] = []
    rects: list[float] = []
    units_list: list[float] = []
    floors_list: list[float] = []
    heights_list: list[float] = []
    features: list[list[float]] = []

    for _, row in gdf.iterrows():
        m = compute_geometry_metrics(row.geometry)
        areas.append(m["footprint_area_m2"])
        aspects.append(m["aspect_ratio"])
        compacts.append(m["compactness"])
        rects.append(m["rectangularity"])
        features.append([m["footprint_area_m2"], m["aspect_ratio"],
                        m["compactness"], m["rectangularity"]])

        # Parse attributes
        units_str = row.get("units")
        if units_str and units_str != "..":
            try:
                units_list.append(float(units_str))
            except (ValueError, TypeError):
                pass
        floors_str = row.get("floors")
        if floors_str and floors_str != "..":
            try:
                floors_list.append(float(floors_str))
            except (ValueError, TypeError):
                pass
        height_str = row.get("height")
        if height_str and height_str != "..":
            try:
                heights_list.append(float(height_str))
            except (ValueError, TypeError):
                pass

        all_murb_metrics.append({
            "province": prov_key,
            "area": m["footprint_area_m2"],
            "aspect_ratio": m["aspect_ratio"],
            "compactness": m["compactness"],
        })

    # Statistics
    area_stats = compute_descriptive_stats(areas, "footprint_area_m2")
    ar_stats = compute_descriptive_stats(aspects, "aspect_ratio")

    prov_result = {
        "province": prov_key,
        "query": config["description"],
        "n_buildings": len(gdf),
        "footprint_area_m2": area_stats,
        "aspect_ratio": ar_stats,
        "compactness": compute_descriptive_stats(compacts, "compactness"),
        "rectangularity": compute_descriptive_stats(rects, "rectangularity"),
    }
    if units_list:
        prov_result["units"] = compute_descriptive_stats(units_list, "units")
    if floors_list:
        prov_result["floors"] = compute_descriptive_stats(floors_list, "floors")
    if heights_list:
        prov_result["height_m"] = compute_descriptive_stats(heights_list, "height_m")

    province_results[prov_key] = prov_result

    print(f"  Area: median={area_stats['median']:.0f} m², "
          f"IQR={area_stats['p25']:.0f}–{area_stats['p75']:.0f}")
    print(f"  AR: median={ar_stats['median']:.2f}")
    if units_list:
        u = compute_descriptive_stats(units_list, "u")
        print(f"  Units: median={u['median']:.0f}, max={u['max']:.0f}")
    if floors_list:
        fl = compute_descriptive_stats(floors_list, "f")
        print(f"  Floors: median={fl['median']:.0f}, max={fl['max']:.0f}")

# --- Combined National MURB Statistics ---
print(f"\n{'='*70}")
print("  COMBINED MULTI-PROVINCE MURB STATISTICS")
print(f"{'='*70}")

total_murbs = len(all_murb_metrics)
all_areas = [m["area"] for m in all_murb_metrics]
all_ar = [m["aspect_ratio"] for m in all_murb_metrics]

combined_stats = {
    "description": "Combined MURB geometry from all data-rich provinces",
    "total_buildings": total_murbs,
    "provinces_included": list(province_results.keys()),
    "footprint_area_m2": compute_descriptive_stats(all_areas, "footprint_area_m2"),
    "aspect_ratio": compute_descriptive_stats(all_ar, "aspect_ratio"),
    "by_province": province_results,
}

nat_area = combined_stats["footprint_area_m2"]
nat_ar = combined_stats["aspect_ratio"]
print(f"\n  Total MURB candidates: {total_murbs:,}")
print(f"  Footprint area: median={nat_area['median']:.0f} m², "
      f"IQR={nat_area['p25']:.0f}–{nat_area['p75']:.0f}, "
      f"mean={nat_area['mean']:.0f} m²")
print(f"  Aspect ratio: median={nat_ar['median']:.2f}, "
      f"IQR={nat_ar['p25']:.2f}–{nat_ar['p75']:.2f}")

# --- National Clustering ---
print(f"\n  Clustering {total_murbs} MURBs into 8 archetypes...")
features_all = np.array([[m["area"], m["aspect_ratio"], m["compactness"]]
                        for m in all_murb_metrics])
cluster_result = cluster_buildings(features_all, n_clusters=8, random_seed=42)

national_archetypes = []
for k in range(cluster_result["n_clusters"]):
    mask = cluster_result["labels"] == k
    cluster_areas = [all_areas[i] for i in range(len(all_areas)) if mask[i]]
    cluster_ar = [all_ar[i] for i in range(len(all_ar)) if mask[i]]
    medoid_idx = cluster_result["medoid_indices"][k]
    nat_arch = {
        "archetype_id": f"NAT-A{k+1:02d}",
        "cluster_size": int(np.sum(mask)),
        "medoid_index": medoid_idx,
        "representative_area_m2": round(all_areas[medoid_idx], 1),
        "representative_aspect_ratio": round(all_ar[medoid_idx], 2),
        "province_of_medoid": all_murb_metrics[medoid_idx]["province"],
        "cluster_area_stats": compute_descriptive_stats(cluster_areas, "area"),
        "cluster_ar_stats": compute_descriptive_stats(cluster_ar, "ar"),
    }
    national_archetypes.append(nat_arch)
    print(f"    {nat_arch['archetype_id']}: n={nat_arch['cluster_size']:>5}, "
          f"area={nat_arch['representative_area_m2']:>7.0f} m², "
          f"AR={nat_arch['representative_aspect_ratio']:.2f} "
          f"[{nat_arch['province_of_medoid']}]")

# Save all outputs
with open(OUTPUT_DIR / "reports" / "national_murb_analysis.json", "w") as f:
    json.dump(combined_stats, f, indent=2, default=str)

arch_output = {
    "description": "National MURB archetypes from multi-province analysis",
    "method": "K-means (k=8) with medoid selection",
    "total_buildings": total_murbs,
    "provinces": list(province_results.keys()),
    "features": ["footprint_area_m2", "aspect_ratio", "compactness"],
    "random_seed": 42,
    "archetypes": national_archetypes,
}
with open(OUTPUT_DIR / "archetypes" / "national_archetypes.json", "w") as f:
    json.dump(arch_output, f, indent=2, default=str)

elapsed_total = time.time() - start
print(f"\n{'='*70}")
print(f"  COMPLETE — {elapsed_total:.0f}s")
print(f"  outputs/reports/national_murb_analysis.json")
print(f"  outputs/archetypes/national_archetypes.json")
print(f"{'='*70}")
