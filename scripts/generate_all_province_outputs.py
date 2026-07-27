"""Generate ALL per-province outputs: stats, archetypes, gbXML, Excel."""

import json
import math
from pathlib import Path

import geopandas as gpd
import numpy as np

from murb_geometry.archetypes.clustering import cluster_buildings
from murb_geometry.excel.workbook import create_summary_workbook
from murb_geometry.gbxml.exporter import export_gbxml
from murb_geometry.gbxml.model import (
    Adjacency,
    BuildingGeometryModel,
    Space,
    Storey,
    Surface,
    SurfaceType,
    Vertex,
)
from murb_geometry.gbxml.validator import validate_gbxml_structure
from murb_geometry.geometry.metrics import compute_geometry_metrics
from murb_geometry.statistics.descriptive import compute_descriptive_stats

OUTPUT = Path("outputs")
(OUTPUT / "reports").mkdir(parents=True, exist_ok=True)
(OUTPUT / "archetypes").mkdir(parents=True, exist_ok=True)
(OUTPUT / "gbxml").mkdir(parents=True, exist_ok=True)
(OUTPUT / "excel").mkdir(parents=True, exist_ok=True)

QUERIES = {
    "NS": ("data/ODB_v3_NS/ODB_v3_NS.gpkg", "units != '..' AND CAST(units AS INTEGER) >= 4"),
    "NB": ("data/ODB_v3_NB/ODB_v3_NB.gpkg", "units != '..' AND CAST(units AS INTEGER) >= 4"),
    "ON_2": ("data/ODB_v3_ON_2/ODB_v3_ON_2.gpkg", "units != '..' AND CAST(units AS INTEGER) >= 4"),
    "ON_3": ("data/ODB_v3_ON_3/ODB_v3_ON_3.gpkg", "units != '..' AND CAST(units AS INTEGER) >= 4"),
    "BC": ("data/ODB_v3_BC/ODB_v3_BC.gpkg", "floors != '..' AND CAST(floors AS INTEGER) >= 4"),
    "AB": (
        "data/ODB_v3_AB/ODB_v3_AB.gpkg",
        "type LIKE '%partment%' OR type LIKE '%ulti%' OR type LIKE '%ondo%'",
    ),
}

all_province_results: dict[str, dict] = {}
all_murbs: list[dict] = []

for prov, (fpath, where) in QUERIES.items():
    print(f"{prov}...", end=" ", flush=True)
    gdf = gpd.read_file(fpath, where=where, rows=3000)
    areas: list[float] = []
    ars: list[float] = []
    comps: list[float] = []
    units_l: list[float] = []
    floors_l: list[float] = []
    features: list[list[float]] = []

    for _, row in gdf.iterrows():
        m = compute_geometry_metrics(row.geometry)
        areas.append(m["footprint_area_m2"])
        ars.append(m["aspect_ratio"])
        comps.append(m["compactness"])
        features.append([m["footprint_area_m2"], m["aspect_ratio"], m["compactness"]])
        all_murbs.append({
            "prov": prov,
            "area": m["footprint_area_m2"],
            "ar": m["aspect_ratio"],
            "comp": m["compactness"],
        })
        u = row.get("units")
        if u and u != "..":
            try:
                units_l.append(float(u))
            except (ValueError, TypeError):
                pass
        f = row.get("floors")
        if f and f != "..":
            try:
                floors_l.append(float(f))
            except (ValueError, TypeError):
                pass

    # Province stats
    prov_stats: dict = {
        "n": len(gdf),
        "footprint_area_m2": compute_descriptive_stats(areas, "area"),
        "aspect_ratio": compute_descriptive_stats(ars, "ar"),
        "compactness": compute_descriptive_stats(comps, "comp"),
    }
    if units_l:
        prov_stats["units"] = compute_descriptive_stats(units_l, "units")
    if floors_l:
        prov_stats["floors"] = compute_descriptive_stats(floors_l, "floors")

    # Province clustering (4 archetypes per province)
    if len(features) >= 4:
        feat_arr = np.array(features)
        cr = cluster_buildings(feat_arr, n_clusters=4, random_seed=42)
        prov_archetypes = []
        for k in range(cr["n_clusters"]):
            mask = cr["labels"] == k
            mi = cr["medoid_indices"][k]
            prov_archetypes.append({
                "id": f"{prov}-A{k + 1:02d}",
                "n": int(np.sum(mask)),
                "area_m2": round(areas[mi], 1),
                "aspect_ratio": round(ars[mi], 2),
            })
        prov_stats["archetypes"] = prov_archetypes

        # Generate gbXML for the most common archetype
        biggest = max(prov_archetypes, key=lambda a: a["n"])
        area = biggest["area_m2"]
        ar = biggest["aspect_ratio"]
        width = math.sqrt(area / max(ar, 1.0))
        length = area / width
        storeys = 4
        fth = 3.0

        all_storeys_model = []
        for i in range(storeys):
            z0 = i * fth
            z1 = z0 + fth
            surfaces = [
                Surface(
                    name=f"S-F{i}",
                    surface_type=SurfaceType.EXTERIOR_WALL,
                    vertices=[
                        Vertex(0, 0, z0), Vertex(length, 0, z0),
                        Vertex(length, 0, z1), Vertex(0, 0, z1),
                    ],
                    area_m2=length * fth,
                ),
                Surface(
                    name=f"N-F{i}",
                    surface_type=SurfaceType.EXTERIOR_WALL,
                    vertices=[
                        Vertex(length, width, z0), Vertex(0, width, z0),
                        Vertex(0, width, z1), Vertex(length, width, z1),
                    ],
                    area_m2=length * fth,
                ),
                Surface(
                    name=f"E-F{i}",
                    surface_type=SurfaceType.EXTERIOR_WALL,
                    vertices=[
                        Vertex(length, 0, z0), Vertex(length, width, z0),
                        Vertex(length, width, z1), Vertex(length, 0, z1),
                    ],
                    area_m2=width * fth,
                ),
                Surface(
                    name=f"W-F{i}",
                    surface_type=SurfaceType.EXTERIOR_WALL,
                    vertices=[
                        Vertex(0, width, z0), Vertex(0, 0, z0),
                        Vertex(0, 0, z1), Vertex(0, width, z1),
                    ],
                    area_m2=width * fth,
                ),
            ]
            if i == 0:
                surfaces.append(Surface(
                    name="Ground",
                    surface_type=SurfaceType.GROUND_FLOOR,
                    adjacency=Adjacency.GROUND,
                    vertices=[
                        Vertex(0, 0, 0), Vertex(length, 0, 0),
                        Vertex(length, width, 0), Vertex(0, width, 0),
                    ],
                    area_m2=area,
                ))
            if i == storeys - 1:
                surfaces.append(Surface(
                    name="Roof",
                    surface_type=SurfaceType.ROOF,
                    adjacency=Adjacency.EXTERIOR,
                    vertices=[
                        Vertex(0, 0, z1), Vertex(length, 0, z1),
                        Vertex(length, width, z1), Vertex(0, width, z1),
                    ],
                    area_m2=area,
                    tilt_deg=0,
                ))
            space = Space(
                name=f"Zone-F{i}",
                surfaces=surfaces,
                floor_area_m2=area,
                volume_m3=area * fth,
            )
            all_storeys_model.append(Storey(
                name=f"Floor {i + 1}",
                level=i,
                floor_to_floor_m=fth,
                elevation_m=z0,
                spaces=[space],
            ))

        model = BuildingGeometryModel(
            name=f"{prov} Representative MURB ({biggest['id']})",
            storeys=all_storeys_model,
            total_floor_area_m2=area * storeys,
            footprint_area_m2=area,
            height_m=storeys * fth,
            num_storeys=storeys,
            construction_method="synthetic_parametric",
            archetype_id=biggest["id"],
        )
        xml = export_gbxml(model)
        xml_path = OUTPUT / "gbxml" / f"{prov.lower()}_archetype.xml"
        xml_path.write_text(xml, encoding="utf-8")
        val = validate_gbxml_structure(xml)
        prov_stats["gbxml"] = {
            "file": str(xml_path),
            "valid": val["valid"],
            "surfaces": val["stats"].get("surfaces", 0),
        }

    all_province_results[prov] = prov_stats
    print(f"n={len(gdf)}, median={prov_stats['footprint_area_m2']['median']:.0f} m2")

# Save per-province results
with open(OUTPUT / "reports" / "all_provinces_murb_analysis.json", "w") as f:
    json.dump(all_province_results, f, indent=2, default=str)

# Excel per province
completeness = [
    {
        "province": p,
        "n_murbs": d["n"],
        "median_area_m2": d["footprint_area_m2"]["median"],
        "p25_area": d["footprint_area_m2"]["p25"],
        "p75_area": d["footprint_area_m2"]["p75"],
        "median_ar": d["aspect_ratio"]["median"],
        "n_archetypes": len(d.get("archetypes", [])),
    }
    for p, d in all_province_results.items()
]
create_summary_workbook(
    OUTPUT / "excel" / "murb_all_provinces.xlsx",
    completeness_data=completeness,
    metadata={
        "Scope": "All provinces with MURB-identifiable data",
        "Total MURBs": str(len(all_murbs)),
        "Provinces": ", ".join(all_province_results.keys()),
    },
)

print(f"\nTotal MURBs across all provinces: {len(all_murbs)}")
nat = compute_descriptive_stats([m["area"] for m in all_murbs], "national")
print(f"National median: {nat['median']:.0f} m2, IQR {nat['p25']:.0f}-{nat['p75']:.0f}")
print(f"\nOutputs:")
print(f"  outputs/reports/all_provinces_murb_analysis.json")
print(f"  outputs/excel/murb_all_provinces.xlsx")
for p in all_province_results:
    xml_path = OUTPUT / "gbxml" / f"{p.lower()}_archetype.xml"
    if xml_path.exists():
        print(f"  outputs/gbxml/{p.lower()}_archetype.xml")
print("Done!")
