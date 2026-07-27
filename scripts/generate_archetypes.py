"""Generate MURB archetypes from NS data using K-means clustering.

Clusters 2000 confirmed MURBs from Nova Scotia by geometry features
and selects representative buildings (medoids) for each archetype.
"""

import json
from pathlib import Path

import geopandas as gpd
import numpy as np

from murb_geometry.archetypes.clustering import cluster_buildings
from murb_geometry.geometry.metrics import compute_geometry_metrics
from murb_geometry.statistics.descriptive import compute_descriptive_stats

print("Loading NS MURBs (units >= 4)...")
gdf = gpd.read_file(
    "data/ODB_v3_NS/ODB_v3_NS.gpkg",
    where="units != '..' AND CAST(units AS INTEGER) >= 4",
    rows=2000,
)
print(f"Loaded {len(gdf)} buildings")

# Compute geometry features
print("Computing geometry metrics...")
metrics_list = []
for _, row in gdf.iterrows():
    m = compute_geometry_metrics(row.geometry)
    m["units"] = float(row.get("units", 0) or 0)
    metrics_list.append(m)

# Build feature matrix for clustering
feature_names = ["footprint_area_m2", "aspect_ratio", "compactness", "rectangularity"]
features = np.array([[m[f] for f in feature_names] for m in metrics_list])

# Cluster into 6 archetypes
print("Clustering into 6 archetypes...")
result = cluster_buildings(features, n_clusters=6, random_seed=42)
labels = result["labels"]
medoid_indices = result["medoid_indices"]

print(f"\nArchetype Results (inertia={result['inertia']:.1f}):")
print("-" * 70)

archetypes = []
for k in range(result["n_clusters"]):
    cluster_mask = labels == k
    cluster_metrics = [metrics_list[i] for i in range(len(metrics_list)) if cluster_mask[i]]
    medoid_idx = medoid_indices[k]
    medoid_metrics = metrics_list[medoid_idx]

    archetype = {
        "archetype_id": f"NS-A{k+1:02d}",
        "cluster_size": int(np.sum(cluster_mask)),
        "medoid_index": medoid_idx,
        "medoid_building_id": gdf.iloc[medoid_idx]["id"],
        "representative_metrics": {
            "footprint_area_m2": round(medoid_metrics["footprint_area_m2"], 1),
            "aspect_ratio": round(medoid_metrics["aspect_ratio"], 2),
            "compactness": round(medoid_metrics["compactness"], 3),
            "rectangularity": round(medoid_metrics["rectangularity"], 3),
        },
        "cluster_statistics": {
            "footprint_area_m2": compute_descriptive_stats(
                [m["footprint_area_m2"] for m in cluster_metrics], "footprint_area_m2"
            ),
            "aspect_ratio": compute_descriptive_stats(
                [m["aspect_ratio"] for m in cluster_metrics], "aspect_ratio"
            ),
        },
    }
    archetypes.append(archetype)

    print(
        f"  {archetype['archetype_id']}: "
        f"n={archetype['cluster_size']:>4}, "
        f"area={medoid_metrics['footprint_area_m2']:>7.0f} m2, "
        f"AR={medoid_metrics['aspect_ratio']:.2f}, "
        f"compact={medoid_metrics['compactness']:.3f}"
    )

# Save
Path("outputs/archetypes").mkdir(parents=True, exist_ok=True)
output = {
    "description": "MURB archetypes derived from Nova Scotia buildings with units >= 4",
    "method": "K-means clustering with medoid selection",
    "n_clusters": result["n_clusters"],
    "n_buildings": len(gdf),
    "features_used": feature_names,
    "random_seed": 42,
    "inertia": result["inertia"],
    "archetypes": archetypes,
}
with open("outputs/archetypes/ns_archetypes.json", "w") as f:
    json.dump(output, f, indent=2, default=str)

print(f"\nSaved: outputs/archetypes/ns_archetypes.json")
