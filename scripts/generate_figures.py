"""Generate publication-quality figures from national run data.

Produces static figures (PNG/HTML) for the methodology report,
using Plotly for interactive charts and static export.
"""

import json
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

OUTPUT_DIR = Path("outputs")
FIGURES_DIR = OUTPUT_DIR / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Load data
inventory = json.loads((OUTPUT_DIR / "reports" / "inventory.json").read_text())
summary = json.loads((OUTPUT_DIR / "reports" / "summary_stats.json").read_text())
classification = json.loads((OUTPUT_DIR / "reports" / "classification_summary.json").read_text())
ns_analysis = json.loads((OUTPUT_DIR / "reports" / "ns_murb_analysis.json").read_text())
archetypes = json.loads((OUTPUT_DIR / "archetypes" / "ns_archetypes.json").read_text())

print("Generating publication figures...")

# --- Figure 1: National Data Completeness Matrix ---
print("  Figure 1: Data completeness heatmap...")

provinces = []
fields = ["type", "floors", "units", "height", "year_built", "address"]
completeness_matrix: list[list[float]] = []

for f in inventory["files"]:
    prov = f["province_territory"]
    # Combine split provinces
    if prov in [p for p, _ in provinces]:
        continue
    provinces.append((prov, f["total_records"]))
    field_map = {fc["field_name"]: fc["completeness_pct"] for fc in f["field_completeness"]}
    row = [field_map.get(field, 0.0) for field in fields]
    completeness_matrix.append(row)

fig1 = go.Figure(data=go.Heatmap(
    z=completeness_matrix,
    x=[f.replace("_", " ").title() for f in fields],
    y=[f"{p} ({r:,})" for p, r in provinces],
    colorscale="RdYlGn",
    zmin=0,
    zmax=100,
    text=[[f"{v:.1f}%" for v in row] for row in completeness_matrix],
    texttemplate="%{text}",
    textfont={"size": 9},
    colorbar={"title": "Completeness (%)"},
))
fig1.update_layout(
    title="Figure 1: Field Completeness by Province — ODB v3",
    title_font_size=14,
    xaxis_title="Attribute Field",
    yaxis_title="Province (record count)",
    width=800,
    height=600,
    yaxis={"autorange": "reversed"},
)
fig1.write_html(str(FIGURES_DIR / "fig1_completeness_heatmap.html"))
fig1.write_image(str(FIGURES_DIR / "fig1_completeness_heatmap.png"), scale=2)

# --- Figure 2: Provincial Footprint Area Distribution ---
print("  Figure 2: Footprint area by province...")

prov_data = summary["by_province"]
prov_names = list(prov_data.keys())
medians = [prov_data[p]["median"] for p in prov_names]
p25s = [prov_data[p]["p25"] for p in prov_names]
p75s = [prov_data[p]["p75"] for p in prov_names]

fig2 = go.Figure()
fig2.add_trace(go.Bar(
    x=prov_names,
    y=medians,
    name="Median",
    marker_color="steelblue",
    error_y=dict(
        type="data",
        symmetric=False,
        array=[p75 - med for p75, med in zip(p75s, medians)],
        arrayminus=[med - p25 for med, p25 in zip(medians, p25s)],
    ),
))
fig2.update_layout(
    title="Figure 2: Building Footprint Area by Province (sampled, n=500 each)",
    title_font_size=14,
    xaxis_title="Province / File",
    yaxis_title="Footprint Area (m²)",
    yaxis={"range": [0, 500]},
    width=900,
    height=500,
    annotations=[dict(
        text="Error bars show IQR (P25–P75). All buildings, not just MURBs.",
        xref="paper", yref="paper", x=0.5, y=-0.15,
        showarrow=False, font=dict(size=10),
    )],
)
fig2.write_html(str(FIGURES_DIR / "fig2_area_by_province.html"))
fig2.write_image(str(FIGURES_DIR / "fig2_area_by_province.png"), scale=2)

# --- Figure 3: NS MURB Footprint Distribution ---
print("  Figure 3: NS MURB footprint distribution...")

ns_stats = ns_analysis["footprint_area_m2"]
# Create synthetic histogram from percentiles
percentiles = [ns_stats["min"], ns_stats["p5"], ns_stats["p10"], ns_stats["p25"],
               ns_stats["median"], ns_stats["p75"], ns_stats["p90"], ns_stats["p95"],
               ns_stats["max"]]
labels = ["Min", "P5", "P10", "P25", "Median", "P75", "P90", "P95", "Max"]

fig3 = go.Figure()
fig3.add_trace(go.Bar(
    x=labels,
    y=percentiles,
    marker_color=["#d62728", "#ff7f0e", "#ff7f0e", "#2ca02c",
                  "#1f77b4", "#2ca02c", "#ff7f0e", "#ff7f0e", "#d62728"],
    text=[f"{v:.0f}" for v in percentiles],
    textposition="outside",
))
fig3.update_layout(
    title=f"Figure 3: NS MURB Footprint Area Distribution (n={ns_analysis['n_buildings']})",
    title_font_size=14,
    xaxis_title="Percentile",
    yaxis_title="Footprint Area (m²)",
    width=800,
    height=500,
    annotations=[dict(
        text=f"Median: {ns_stats['median']:.0f} m² | Mean: {ns_stats['mean']:.0f} m² | "
             f"IQR: {ns_stats['p25']:.0f}–{ns_stats['p75']:.0f} m²",
        xref="paper", yref="paper", x=0.5, y=1.05,
        showarrow=False, font=dict(size=11),
    )],
)
fig3.write_html(str(FIGURES_DIR / "fig3_ns_murb_area_distribution.html"))
fig3.write_image(str(FIGURES_DIR / "fig3_ns_murb_area_distribution.png"), scale=2)

# --- Figure 4: Archetype Comparison ---
print("  Figure 4: Archetype comparison...")

arch_ids = [a["archetype_id"] for a in archetypes["archetypes"]]
arch_areas = [a["representative_area_m2"] for a in archetypes["archetypes"]]
arch_ar = [a["representative_aspect_ratio"] for a in archetypes["archetypes"]]
arch_n = [a["cluster_size"] for a in archetypes["archetypes"]]

fig4 = make_subplots(rows=1, cols=2, subplot_titles=("Footprint Area", "Aspect Ratio"))
fig4.add_trace(go.Bar(
    x=arch_ids, y=arch_areas, name="Area (m²)",
    marker_color="steelblue",
    text=[f"{a:.0f}" for a in arch_areas],
    textposition="outside",
), row=1, col=1)
fig4.add_trace(go.Bar(
    x=arch_ids, y=arch_ar, name="Aspect Ratio",
    marker_color="coral",
    text=[f"{a:.2f}" for a in arch_ar],
    textposition="outside",
), row=1, col=2)
fig4.update_layout(
    title="Figure 4: NS MURB Archetype Representative Metrics (6 clusters)",
    title_font_size=14,
    showlegend=False,
    width=900,
    height=450,
    annotations=[dict(
        text="Cluster sizes: " + ", ".join(f"{i}: n={n}" for i, n in zip(arch_ids, arch_n)),
        xref="paper", yref="paper", x=0.5, y=-0.12,
        showarrow=False, font=dict(size=10),
    )],
)
fig4.update_yaxes(title_text="Area (m²)", row=1, col=1)
fig4.update_yaxes(title_text="Aspect Ratio", row=1, col=2)
fig4.write_html(str(FIGURES_DIR / "fig4_archetype_comparison.html"))
fig4.write_image(str(FIGURES_DIR / "fig4_archetype_comparison.png"), scale=2)

# --- Figure 5: Classification Distribution ---
print("  Figure 5: National classification...")

class_data = classification["national_totals"]
labels_c = list(class_data.keys())
values_c = list(class_data.values())
colors = {"non_murb": "#aec7e8", "insufficient_information": "#ffbb78",
           "possible_murb": "#98df8a", "probable_murb": "#ff9896",
           "high_confidence_murb": "#c5b0d5", "confirmed_murb": "#c49c94"}

fig5 = go.Figure(data=[go.Pie(
    labels=[l.replace("_", " ").title() for l in labels_c],
    values=values_c,
    marker_colors=[colors.get(l, "#999") for l in labels_c],
    textinfo="label+percent",
    hole=0.3,
)])
fig5.update_layout(
    title="Figure 5: National MURB Classification (sampled, n=7,500)",
    title_font_size=14,
    width=700,
    height=500,
    annotations=[dict(
        text="Random sampling of first 500 records per file.\n"
             "MURBs are rare in untargeted samples.",
        xref="paper", yref="paper", x=0.5, y=-0.1,
        showarrow=False, font=dict(size=10),
    )],
)
fig5.write_html(str(FIGURES_DIR / "fig5_classification_pie.html"))
fig5.write_image(str(FIGURES_DIR / "fig5_classification_pie.png"), scale=2)

print(f"\n  All figures saved to: {FIGURES_DIR}/")
print("  Files: fig1-fig5 (.html interactive + .png static)")
