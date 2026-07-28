"""DEPRECATED — Complete national MURB analysis — per-province clustering with merged provinces.

⚠️ THIS SCRIPT IS DEPRECATED. Use the production pipeline instead:

    murb-geometry run-all

Or directly:

    python scripts/national_full_run.py

This script uses MAX_PER_FILE=2000 (an arbitrary row cap that violates the
full-population analytical rule) and fixed k=5/k=8 cluster counts without
empirical justification.

The replacement (src/murb_geometry/pipeline.py) processes complete populations
with Option C multi-pathway classification.
"""

raise SystemExit(
    "DEPRECATED: This script uses arbitrary row caps (MAX_PER_FILE=2000) and "
    "fixed cluster counts.\n"
    "Use 'murb-geometry run-all' or 'python scripts/national_full_run.py' instead.\n"
    "See docs/methodology.md for the current pipeline methodology."
)


def build_gbxml_box(name: str, area: float, ar: float, storeys: int = 4, fth: float = 3.0) -> str:
    """Generate a gbXML box building from area and aspect ratio."""
    width = math.sqrt(area / max(ar, 1.0))
    length = area / width
    height = storeys * fth

    model_storeys = []
    for i in range(storeys):
        z0, z1 = i * fth, (i + 1) * fth
        surfaces = [
            Surface(name=f"South-F{i}", surface_type=SurfaceType.EXTERIOR_WALL,
                    vertices=[Vertex(0,0,z0), Vertex(length,0,z0), Vertex(length,0,z1), Vertex(0,0,z1)],
                    area_m2=length*fth, azimuth_deg=180),
            Surface(name=f"North-F{i}", surface_type=SurfaceType.EXTERIOR_WALL,
                    vertices=[Vertex(length,width,z0), Vertex(0,width,z0), Vertex(0,width,z1), Vertex(length,width,z1)],
                    area_m2=length*fth, azimuth_deg=0),
            Surface(name=f"East-F{i}", surface_type=SurfaceType.EXTERIOR_WALL,
                    vertices=[Vertex(length,0,z0), Vertex(length,width,z0), Vertex(length,width,z1), Vertex(length,0,z1)],
                    area_m2=width*fth, azimuth_deg=90),
            Surface(name=f"West-F{i}", surface_type=SurfaceType.EXTERIOR_WALL,
                    vertices=[Vertex(0,width,z0), Vertex(0,0,z0), Vertex(0,0,z1), Vertex(0,width,z1)],
                    area_m2=width*fth, azimuth_deg=270),
        ]
        if i == 0:
            surfaces.append(Surface(name="Ground", surface_type=SurfaceType.GROUND_FLOOR,
                            adjacency=Adjacency.GROUND,
                            vertices=[Vertex(0,0,0), Vertex(length,0,0), Vertex(length,width,0), Vertex(0,width,0)],
                            area_m2=area))
        if i == storeys - 1:
            surfaces.append(Surface(name="Roof", surface_type=SurfaceType.ROOF,
                            adjacency=Adjacency.EXTERIOR,
                            vertices=[Vertex(0,0,z1), Vertex(length,0,z1), Vertex(length,width,z1), Vertex(0,width,z1)],
                            area_m2=area, tilt_deg=0))
        space = Space(name=f"Zone-F{i}", surfaces=surfaces, floor_area_m2=area, volume_m3=area*fth)
        model_storeys.append(Storey(name=f"Floor {i+1}", level=i, floor_to_floor_m=fth, elevation_m=z0, spaces=[space]))

    model = BuildingGeometryModel(
        name=name, storeys=model_storeys,
        total_floor_area_m2=area*storeys, footprint_area_m2=area,
        height_m=height, num_storeys=storeys,
        construction_method="synthetic_parametric",
    )
    return export_gbxml(model)


# ═══════════════════════════════════════════════════════════════
print("=" * 70)
print("  FULL NATIONAL MURB ANALYSIS — MERGED PROVINCES")
print(f"  {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}")
print("=" * 70)

all_province_data: dict[str, dict] = {}
national_murbs: list[dict] = []

for prov, file_queries in PROVINCE_FILES.items():
    print(f"\n{'━' * 50}")
    print(f"  {prov}")

    # Load and merge all files for this province
    gdfs = []
    for fpath, where in file_queries:
        print(f"    Loading: {Path(fpath).name}...", end=" ", flush=True)
        try:
            gdf = gpd.read_file(fpath, where=where, rows=MAX_PER_FILE)
            print(f"{len(gdf)} records")
            gdfs.append(gdf)
        except Exception as e:
            print(f"ERROR: {e}")

    if not gdfs:
        print(f"    No data loaded for {prov} — skipping")
        continue

    import pandas as pd
    gdf_merged = pd.concat(gdfs, ignore_index=True) if len(gdfs) > 1 else gdfs[0]
    gdf_merged = gpd.GeoDataFrame(gdf_merged, geometry="geometry")
    print(f"    Total for {prov}: {len(gdf_merged)} MURBs")

    # Compute metrics
    areas: list[float] = []
    ars: list[float] = []
    comps: list[float] = []
    rects: list[float] = []
    units_l: list[float] = []
    floors_l: list[float] = []
    features: list[list[float]] = []

    for _, row in gdf_merged.iterrows():
        m = compute_geometry_metrics(row.geometry)
        areas.append(m["footprint_area_m2"])
        ars.append(m["aspect_ratio"])
        comps.append(m["compactness"])
        rects.append(m["rectangularity"])
        features.append([m["footprint_area_m2"], m["aspect_ratio"], m["compactness"], m["rectangularity"]])
        national_murbs.append({"prov": prov, "area": m["footprint_area_m2"], "ar": m["aspect_ratio"], "comp": m["compactness"]})

        for field, lst in [("units", units_l), ("floors", floors_l)]:
            val = row.get(field)
            if val and val != "..":
                try:
                    lst.append(float(val))
                except (ValueError, TypeError):
                    pass

    # Statistics
    prov_result: dict = {
        "province": prov,
        "n_buildings": len(gdf_merged),
        "n_files_merged": len(file_queries),
        "footprint_area_m2": compute_descriptive_stats(areas, "footprint_area_m2"),
        "aspect_ratio": compute_descriptive_stats(ars, "aspect_ratio"),
        "compactness": compute_descriptive_stats(comps, "compactness"),
        "rectangularity": compute_descriptive_stats(rects, "rectangularity"),
    }
    if units_l:
        prov_result["units"] = compute_descriptive_stats(units_l, "units")
    if floors_l:
        prov_result["floors"] = compute_descriptive_stats(floors_l, "floors")

    area_s = prov_result["footprint_area_m2"]
    print(f"    Area: median={area_s['median']:.0f} m², IQR={area_s['p25']:.0f}–{area_s['p75']:.0f}")
    print(f"    AR: median={prov_result['aspect_ratio']['median']:.2f}")

    # Clustering (5 archetypes per province)
    n_clusters = min(5, len(features) // 3)
    if n_clusters >= 2:
        feat_arr = np.array(features)
        cr = cluster_buildings(feat_arr, n_clusters=n_clusters, random_seed=42)
        prov_archetypes = []
        for k in range(cr["n_clusters"]):
            mask = cr["labels"] == k
            mi = cr["medoid_indices"][k]
            cluster_areas = [areas[i] for i in range(len(areas)) if mask[i]]
            arch = {
                "id": f"{prov}-A{k+1:02d}",
                "n": int(np.sum(mask)),
                "pct": round(100 * int(np.sum(mask)) / len(areas), 1),
                "medoid_area_m2": round(areas[mi], 1),
                "medoid_aspect_ratio": round(ars[mi], 2),
                "medoid_compactness": round(comps[mi], 3),
                "cluster_median_area": round(float(np.median(cluster_areas)), 1),
            }
            prov_archetypes.append(arch)
            print(f"      {arch['id']}: n={arch['n']:>4} ({arch['pct']:>4.1f}%), "
                  f"area={arch['medoid_area_m2']:>6.0f} m², AR={arch['medoid_aspect_ratio']:.2f}")
        prov_result["archetypes"] = prov_archetypes

        # gbXML for each archetype
        for arch in prov_archetypes:
            xml = build_gbxml_box(
                f"{prov} Archetype {arch['id']} ({arch['n']} buildings)",
                arch["medoid_area_m2"],
                arch["medoid_aspect_ratio"],
            )
            xml_path = OUTPUT / "gbxml" / f"{prov.lower()}_{arch['id'].lower().replace('-','_')}.xml"
            xml_path.write_text(xml, encoding="utf-8")
            val = validate_gbxml_structure(xml)
            arch["gbxml_file"] = str(xml_path)
            arch["gbxml_valid"] = val["valid"]

    all_province_data[prov] = prov_result

# ═══════════════════════════════════════════════════════════════
# NATIONAL COMBINED
print(f"\n{'═' * 70}")
print(f"  NATIONAL COMBINED: {len(national_murbs):,} MURBs from {len(all_province_data)} provinces")
print(f"{'═' * 70}")

nat_areas = [m["area"] for m in national_murbs]
nat_ars = [m["ar"] for m in national_murbs]
nat_stats = {
    "total_murbs": len(national_murbs),
    "provinces": list(all_province_data.keys()),
    "footprint_area_m2": compute_descriptive_stats(nat_areas, "footprint_area_m2"),
    "aspect_ratio": compute_descriptive_stats(nat_ars, "aspect_ratio"),
}
ns = nat_stats["footprint_area_m2"]
print(f"  Footprint: median={ns['median']:.0f} m², IQR={ns['p25']:.0f}–{ns['p75']:.0f}, mean={ns['mean']:.0f}")
print(f"  AR: median={nat_stats['aspect_ratio']['median']:.2f}")

# National clustering (8 archetypes)
print("  Clustering nationally (k=8)...")
feat_nat = np.array([[m["area"], m["ar"], m["comp"]] for m in national_murbs])
cr_nat = cluster_buildings(feat_nat, n_clusters=8, random_seed=42)
national_archetypes = []
for k in range(cr_nat["n_clusters"]):
    mask = cr_nat["labels"] == k
    mi = cr_nat["medoid_indices"][k]
    national_archetypes.append({
        "id": f"NAT-A{k+1:02d}",
        "n": int(np.sum(mask)),
        "pct": round(100 * int(np.sum(mask)) / len(national_murbs), 1),
        "medoid_area_m2": round(nat_areas[mi], 1),
        "medoid_ar": round(nat_ars[mi], 2),
        "province_of_medoid": national_murbs[mi]["prov"],
    })
    a = national_archetypes[-1]
    print(f"    {a['id']}: n={a['n']:>5} ({a['pct']:>4.1f}%), "
          f"area={a['medoid_area_m2']:>6.0f} m², AR={a['medoid_ar']:.2f} [{a['province_of_medoid']}]")

nat_stats["archetypes"] = national_archetypes

# ═══════════════════════════════════════════════════════════════
# SAVE ALL REPORTS
print("\n  Saving reports...")
full_output = {
    "generated_at": datetime.now(UTC).isoformat(),
    "description": "Complete per-province MURB analysis with merged split files",
    "national": nat_stats,
    "by_province": all_province_data,
}
with open(OUTPUT / "reports" / "complete_analysis.json", "w") as f:
    json.dump(full_output, f, indent=2, default=str)

# ═══════════════════════════════════════════════════════════════
# FIGURES
print("  Generating figures...")

# Fig A: Per-province median area comparison
prov_names = list(all_province_data.keys())
medians = [all_province_data[p]["footprint_area_m2"]["median"] for p in prov_names]
p25s = [all_province_data[p]["footprint_area_m2"]["p25"] for p in prov_names]
p75s = [all_province_data[p]["footprint_area_m2"]["p75"] for p in prov_names]
counts = [all_province_data[p]["n_buildings"] for p in prov_names]

fig_a = go.Figure()
fig_a.add_trace(go.Bar(
    x=prov_names, y=medians, name="Median Area",
    marker_color="steelblue",
    text=[f"{m:.0f}" for m in medians], textposition="outside",
    error_y=dict(type="data", symmetric=False,
                 array=[p75 - med for p75, med in zip(p75s, medians)],
                 arrayminus=[med - p25 for med, p25 in zip(medians, p25s)]),
))
fig_a.update_layout(
    title="MURB Footprint Area by Province (Median + IQR)",
    xaxis_title="Province", yaxis_title="Footprint Area (m²)",
    width=800, height=500,
    annotations=[dict(text=f"n = {', '.join(f'{p}: {n:,}' for p, n in zip(prov_names, counts))}",
                     xref="paper", yref="paper", x=0.5, y=-0.12, showarrow=False, font=dict(size=9))],
)
fig_a.write_image(str(OUTPUT / "figures" / "province_murb_area.png"), scale=2)
fig_a.write_html(str(OUTPUT / "figures" / "province_murb_area.html"))

# Fig B: National archetype scatter
arch_areas = [a["medoid_area_m2"] for a in national_archetypes]
arch_ars = [a["medoid_ar"] for a in national_archetypes]
arch_sizes = [a["n"] for a in national_archetypes]
arch_labels = [a["id"] for a in national_archetypes]

fig_b = go.Figure()
fig_b.add_trace(go.Scatter(
    x=arch_areas, y=arch_ars, mode="markers+text",
    marker=dict(size=[max(10, n/50) for n in arch_sizes], color="coral", opacity=0.7),
    text=arch_labels, textposition="top center",
))
fig_b.update_layout(
    title="National MURB Archetypes (8 clusters)",
    xaxis_title="Footprint Area (m²)", yaxis_title="Aspect Ratio",
    width=800, height=500,
)
fig_b.write_image(str(OUTPUT / "figures" / "national_archetypes_scatter.png"), scale=2)
fig_b.write_html(str(OUTPUT / "figures" / "national_archetypes_scatter.html"))

# Fig C: Province clustering heatmap
fig_c_data = []
for prov, data in all_province_data.items():
    if "archetypes" in data:
        for arch in data["archetypes"]:
            fig_c_data.append({"Province": prov, "Archetype": arch["id"],
                             "Area": arch["medoid_area_m2"], "AR": arch["medoid_aspect_ratio"],
                             "Count": arch["n"]})

if fig_c_data:
    fig_c = make_subplots(rows=1, cols=2, subplot_titles=("Footprint Area by Archetype", "Aspect Ratio by Archetype"))
    for prov in all_province_data:
        prov_archs = [d for d in fig_c_data if d["Province"] == prov]
        if prov_archs:
            fig_c.add_trace(go.Bar(x=[a["Archetype"] for a in prov_archs],
                                  y=[a["Area"] for a in prov_archs], name=prov), row=1, col=1)
            fig_c.add_trace(go.Bar(x=[a["Archetype"] for a in prov_archs],
                                  y=[a["AR"] for a in prov_archs], name=prov, showlegend=False), row=1, col=2)
    fig_c.update_layout(title="Per-Province Archetype Comparison", width=1200, height=500, barmode="group")
    fig_c.write_image(str(OUTPUT / "figures" / "province_archetypes_comparison.png"), scale=2)
    fig_c.write_html(str(OUTPUT / "figures" / "province_archetypes_comparison.html"))

# ═══════════════════════════════════════════════════════════════
# EXCEL
print("  Generating Excel...")
excel_data = [
    {
        "Province": p, "MURBs": d["n_buildings"],
        "Files Merged": d["n_files_merged"],
        "Median Area (m2)": d["footprint_area_m2"]["median"],
        "P25 Area": d["footprint_area_m2"]["p25"],
        "P75 Area": d["footprint_area_m2"]["p75"],
        "Median AR": d["aspect_ratio"]["median"],
        "Archetypes": len(d.get("archetypes", [])),
    }
    for p, d in all_province_data.items()
]
create_summary_workbook(
    OUTPUT / "excel" / "complete_murb_analysis.xlsx",
    completeness_data=excel_data,
    summary_stats=[nat_stats["footprint_area_m2"], nat_stats["aspect_ratio"]],
    metadata={
        "Analysis": "Complete per-province MURB characterization",
        "Total MURBs": str(len(national_murbs)),
        "Provinces": ", ".join(all_province_data.keys()),
        "Split files merged": "ON (3 files → 1), QC excluded (no units/type data)",
        "National archetypes": "8 (K-means)",
        "Generated": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
    },
)

# ═══════════════════════════════════════════════════════════════
print(f"\n{'═' * 70}")
print(f"  COMPLETE")
print(f"  Total MURBs: {len(national_murbs):,}")
print(f"  Provinces: {', '.join(all_province_data.keys())}")
print(f"  Per-province archetypes: {sum(len(d.get('archetypes',[])) for d in all_province_data.values())}")
print(f"  National archetypes: 8")
print(f"  gbXML files: {len(list((OUTPUT / 'gbxml').glob('*.xml')))}")
print(f"  Figures: {len(list((OUTPUT / 'figures').glob('*.png')))}")
print(f"{'═' * 70}")
