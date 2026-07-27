"""Generate the methodology report from national run data."""

import json
from datetime import datetime, UTC
from pathlib import Path

OUTPUT_DIR = Path("outputs")

# Load all results
inventory = json.loads((OUTPUT_DIR / "reports" / "inventory.json").read_text())
summary = json.loads((OUTPUT_DIR / "reports" / "summary_stats.json").read_text())
classification = json.loads((OUTPUT_DIR / "reports" / "classification_summary.json").read_text())
ns_analysis = json.loads((OUTPUT_DIR / "reports" / "ns_murb_analysis.json").read_text())
archetypes = json.loads((OUTPUT_DIR / "archetypes" / "ns_archetypes.json").read_text())

# Build report
report_lines = []


def h1(text: str) -> None:
    report_lines.append(f"\n{'='*70}\n{text}\n{'='*70}\n")


def h2(text: str) -> None:
    report_lines.append(f"\n{text}\n{'-'*len(text)}\n")


def p(text: str) -> None:
    report_lines.append(text + "\n")


def table(headers: list[str], rows: list[list[str]], widths: list[int] | None = None) -> None:
    if not widths:
        widths = [max(len(h), max((len(r[i]) for r in rows), default=0)) + 2 for i, h in enumerate(headers)]
    header_line = "".join(h.ljust(w) for h, w in zip(headers, widths))
    report_lines.append(header_line + "\n")
    report_lines.append("-" * sum(widths) + "\n")
    for row in rows:
        report_lines.append("".join(c.ljust(w) for c, w in zip(row, widths)) + "\n")
    report_lines.append("\n")


# === REPORT ===
h1("CANADIAN MURB GEOMETRY ANALYSIS — METHODOLOGY REPORT")
p(f"Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}")
p("Software: murb-geometry v0.1.0")
p("Data: Statistics Canada Open Database of Buildings v3")
p("Licence: Open Government Licence — Canada")

h1("1. EXECUTIVE SUMMARY")
p(f"This report documents the national analytical workflow applied to {inventory['total_records']:,} "
  f"building footprint records from the Statistics Canada Open Database of Buildings (ODB v3), "
  f"comprising {inventory['total_files']} GeoPackage files totalling {inventory['total_size_mb']:.0f} MB.")
p("")
p("Key findings:")
p(f"  • National median building footprint area: {summary['footprint_area_m2']['median']:.0f} m²")
p(f"  • National median aspect ratio: {summary['aspect_ratio']['median']:.2f}")
p(f"  • Nova Scotia confirmed MURBs (units >= 4): {ns_analysis['n_buildings']:,}")
ns_s = ns_analysis["footprint_area_m2"]
p(f"  • NS MURB median footprint: {ns_s['median']:.0f} m² (IQR {ns_s['p25']:.0f}–{ns_s['p75']:.0f})")
p(f"  • NS MURB median aspect ratio: {ns_analysis['aspect_ratio']['median']:.2f}")
p(f"  • NS MURB median dwelling units: {ns_analysis['units']['median']:.0f}")
p(f"  • Representative archetypes generated: {len(archetypes['archetypes'])}")

h1("2. DATA SOURCE")
h2("2.1 Overview")
p("Source: Statistics Canada Open Database of Buildings, Version 3")
p("Format: GeoPackage (.gpkg)")
p("CRS: EPSG:3347 (NAD83 / Statistics Canada Lambert)")
p("Missing value encoding: '..' (two periods)")
p("All attribute fields stored as TEXT (require parsing)")

h2("2.2 National Coverage")
table(
    ["Province", "Records", "Size(MB)", "Type%", "Floors%", "Units%", "Height%"],
    [[f["province_territory"],
      f"{f['total_records']:,}",
      f"{f['file_size_mb']:.0f}",
      f"{next((fc['completeness_pct'] for fc in f['field_completeness'] if fc['field_name'] == 'type'), 0):.1f}",
      f"{next((fc['completeness_pct'] for fc in f['field_completeness'] if fc['field_name'] == 'floors'), 0):.1f}",
      f"{next((fc['completeness_pct'] for fc in f['field_completeness'] if fc['field_name'] == 'units'), 0):.1f}",
      f"{next((fc['completeness_pct'] for fc in f['field_completeness'] if fc['field_name'] == 'height'), 0):.1f}",
      ] for f in inventory["files"]],
    [12, 12, 10, 8, 9, 8, 9],
)

p(f"TOTAL: {inventory['total_records']:,} records across {inventory['total_files']} files")

h2("2.3 Key Data Limitations")
p("1. Attribute completeness varies dramatically by province (0–95%)")
p("2. 'Automatically Extracted Buildings' (satellite-derived) have geometry only")
p("3. Only Nova Scotia has >20% unit-count coverage")
p("4. Ontario and BC have the richest floor/height data (3–27%)")
p("5. Building-type classifications are source-specific and not standardized")
p("6. Footprints may include podiums, garages, and additions")
p("7. Coverage is non-random (depends on municipal open-data policies)")

h1("3. METHODOLOGY")
h2("3.1 Data Ingestion")
p("• Recursive GeoPackage discovery under data/ directory")
p("• SQLite-based metadata inspection (no full data load for inventory)")
p("• pyogrio for CRS and schema verification")
p("• Field completeness calculated per-province via SQL COUNT queries")

h2("3.2 Geometry Metrics")
p("All calculations performed in EPSG:3347 (projected, metric units).")
p("")
p("Metrics computed:")
p("  • Footprint area (m²): polygon.area")
p("  • Perimeter (m): polygon.length")
p("  • Minimum Rotated Rectangle (MRR): shapely minimum_rotated_rectangle")
p("  • Dimensions: major/minor axis of MRR")
p("  • Aspect ratio: MRR_length / MRR_width (always >= 1)")
p("  • Orientation: azimuth of major axis from north [0°, 180°)")
p("  • Compactness (Polsby-Popper): 4*pi * area / perimeter^2")
p("  • Rectangularity: area / MRR_area")
p("  • Convexity: area / convex_hull_area")
p("  • Holes: count and area of interior rings")
p("  • Components: count of disconnected polygon parts")

h2("3.3 MURB Classification")
p("Evidence-based classification with priority-ordered rules:")
p("")
p("  R001: Explicit apartment/multi-residential type → confirmed_murb (1.0)")
p("  R002: Dwelling units >= 4 → high_confidence_murb (0.85)")
p("  R003: Floors >= 4 AND area >= 400 m² → probable_murb (0.70)")
p("  R004: Area >= 600 m² AND residential type → possible_murb (0.50)")
p("  R005: Height >= 12 m → possible_murb (0.45)")
p("  R010: Explicit non-MURB type → non_murb (0.0)")
p("  R011: Footprint < 200 m² → non_murb (0.0)")
p("  R999: No matching rule → insufficient_information (null)")
p("")
p("Minimum MURB unit threshold: 4 dwelling units (configurable)")

h2("3.4 Archetype Generation")
p("Method: K-means clustering with medoid selection")
p(f"Features: {', '.join(archetypes['features'])}")
p("Preprocessing: StandardScaler normalization")
p("Number of clusters: 6 (configurable)")
p("Random seed: 42 (reproducible)")
p("")
p("The medoid (most central actual building) is selected as the")
p("representative for each cluster — NOT an averaged polygon.")

h2("3.5 gbXML Export")
p("Intermediate building geometry model exported to gbXML 7.03:")
p("  • Rectangular extrusion from MRR dimensions")
p("  • Storey-by-storey surface generation")
p("  • Proper surface types (ExteriorWall, Roof, UndergroundSlab)")
p("  • Floor-to-floor height: 3.0 m (configurable)")
p("  • WWR by orientation: N=0.30, E=0.30, S=0.40, W=0.30 (assumed)")

h1("4. RESULTS")
h2("4.1 National Building Footprint Statistics")
stats = summary["footprint_area_m2"]
p(f"Sample size: {stats['count']} buildings (500 per file × 15 files)")
p(f"Valid records: {stats['valid_count']}")
p(f"Min: {stats['min']:.0f} m² | Max: {stats['max']:.0f} m²")
p(f"Mean: {stats['mean']:.0f} m² | Median: {stats['median']:.0f} m²")
p(f"Std: {stats['std']:.0f} m²")
p(f"P5: {stats['p5']:.0f} | P25: {stats['p25']:.0f} | P75: {stats['p75']:.0f} | P95: {stats['p95']:.0f} m²")
p(f"IQR: {stats['iqr']:.0f} m²")

h2("4.2 Nova Scotia MURB Characterization")
p(f"Population: {ns_analysis['n_buildings']:,} buildings with units >= 4")
p(f"Source: ODB_v3_NS.gpkg, SQL-filtered on units field")
p("")
ns_a = ns_analysis["footprint_area_m2"]
ns_ar = ns_analysis["aspect_ratio"]
ns_u = ns_analysis["units"]
table(
    ["Metric", "Min", "P25", "Median", "P75", "Max", "Mean", "Std"],
    [
        ["Area (m²)", f"{ns_a['min']:.0f}", f"{ns_a['p25']:.0f}", f"{ns_a['median']:.0f}",
         f"{ns_a['p75']:.0f}", f"{ns_a['max']:.0f}", f"{ns_a['mean']:.0f}", f"{ns_a['std']:.0f}"],
        ["Aspect Ratio", f"{ns_ar['min']:.2f}", f"{ns_ar['p25']:.2f}", f"{ns_ar['median']:.2f}",
         f"{ns_ar['p75']:.2f}", f"{ns_ar['max']:.2f}", f"{ns_ar['mean']:.2f}", f"{ns_ar['std']:.2f}"],
        ["Units", f"{ns_u['min']:.0f}", f"{ns_u['p25']:.0f}", f"{ns_u['median']:.0f}",
         f"{ns_u['p75']:.0f}", f"{ns_u['max']:.0f}", f"{ns_u['mean']:.0f}", f"{ns_u['std']:.0f}"],
    ],
    [14, 8, 8, 8, 8, 8, 8, 8],
)

h2("4.3 Representative Archetypes")
table(
    ["Archetype", "Count", "Area(m²)", "AR", "Description"],
    [[a["archetype_id"], str(a["cluster_size"]),
      f"{a['representative_area_m2']:.0f}",
      f"{a['representative_aspect_ratio']:.2f}",
      "Small compact" if a["representative_area_m2"] < 300 else
      ("Medium" if a["representative_area_m2"] < 800 else "Large") +
      (" elongated" if a["representative_aspect_ratio"] > 2.5 else " mid-ratio" if a["representative_aspect_ratio"] > 1.8 else " compact")]
     for a in archetypes["archetypes"]],
    [12, 8, 10, 6, 20],
)

h2("4.4 Classification Results")
class_nat = classification["national_totals"]
total_sampled = sum(class_nat.values())
p(f"National sample: {total_sampled} buildings (500 per file × 15 files)")
p("Note: Random sampling of first records per file. MURBs are concentrated")
p("in specific data-rich portions of provincial files.")
p("")
for level, count in sorted(class_nat.items(), key=lambda x: -x[1]):
    p(f"  {level.replace('_', ' ').title()}: {count} ({100*count/total_sampled:.1f}%)")

h1("5. LIMITATIONS")
p("1. FOOTPRINT ≠ FLOOR PLATE: Ground-level footprints may include podiums,")
p("   garages, and additions that differ from typical upper-floor plates.")
p("")
p("2. NO WINDOW DATA: WWR values are archetypal assumptions, not observed.")
p("")
p("3. GEOGRAPHIC BIAS: Only NS has sufficient unit-count data for direct MURB")
p("   identification. National MURB statistics are dominated by data-rich regions.")
p("")
p("4. SAMPLING LIMITATIONS: The national geometry metrics use 500 records per")
p("   file from the beginning of each file, which may not be representative")
p("   of the full provincial dataset.")
p("")
p("5. CLASSIFICATION COVERAGE: Random sampling finds almost no MURBs (1/7500)")
p("   because apartments are a tiny fraction of all buildings. Targeted SQL")
p("   queries on attribute-rich records are necessary.")
p("")
p("6. SINGLE-PROVINCE ARCHETYPES: The 6 archetypes are derived from NS only.")
p("   National archetypes require multi-province MURB identification first.")
p("")
p("7. STOREY ASSUMPTIONS: Floor-to-floor height (3.0 m) and storey count are")
p("   assumptions for most buildings. Only 0–9% have observed floor counts.")

h1("6. REPRODUCIBILITY")
p("All results are reproducible with:")
p("  • Software: murb-geometry v0.1.0")
p("  • Python: 3.12+")
p("  • Configuration: config/default.yaml")
p("  • Random seed: 42")
p("  • Data: Statistics Canada ODB v3 GeoPackage files")
p("")
p("Regeneration command:")
p("  python scripts/national_run.py")
p("")
p("Figures:")
p("  python scripts/generate_figures.py")

h1("7. REFERENCES")
p("1. Statistics Canada. Open Database of Buildings, Version 3.")
p("   https://www.statcan.gc.ca/en/lode/databases/odb")
p("")
p("2. Green Building XML (gbXML) Schema, Version 7.03.")
p("   http://www.gbxml.org/schema")
p("")
p("3. OpenStudio. National Renewable Energy Laboratory.")
p("   https://openstudio.net/")
p("")
p("4. EnergyPlus. U.S. Department of Energy.")
p("   https://energyplus.net/")

# Write report
report_text = "".join(report_lines)
(OUTPUT_DIR / "reports").mkdir(parents=True, exist_ok=True)
with open(OUTPUT_DIR / "reports" / "methodology_report.txt", "w", encoding="utf-8") as f:
    f.write(report_text)

print(f"Methodology report saved: outputs/reports/methodology_report.txt")
print(f"Length: {len(report_text)} characters")
