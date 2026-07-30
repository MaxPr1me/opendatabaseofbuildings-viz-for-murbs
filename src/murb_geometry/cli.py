"""Command-line interface for murb-geometry.

Uses typer for structured CLI commands supporting the full analytical workflow.
"""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from murb_geometry.config import load_config

app = typer.Typer(
    name="murb-geometry",
    help="Canadian MURB Geometry Analysis — characterize representative building geometries.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def inventory(
    config: str = typer.Option("config/default.yaml", help="Configuration file path"),
    data_dir: str | None = typer.Option(None, help="Override data directory"),
    output: str | None = typer.Option(None, help="Output JSON path"),
    no_hash: bool = typer.Option(False, help="Skip SHA-256 hash computation"),
) -> None:
    """Discover and inventory all GeoPackage files in the data directory."""
    from murb_geometry.ingestion.inventory import run_inventory

    cfg = load_config(config_path=config, local_path="config/local.yaml")
    root = Path(data_dir) if data_dir else cfg.paths.data_dir
    output_path = Path(output) if output else Path("outputs/reports/inventory.json")

    console.print(f"[bold]Scanning:[/bold] {root}")
    report = run_inventory(
        data_dir=root,
        output_path=output_path,
        missing_markers=cfg.input.missing_value_markers,
        compute_hashes=not no_hash,
    )

    # Display summary table
    table = Table(title="GeoPackage Inventory")
    table.add_column("File", style="cyan")
    table.add_column("Province", style="green")
    table.add_column("Records", justify="right")
    table.add_column("Size (MB)", justify="right")
    table.add_column("Sources", justify="right")
    table.add_column("Type %", justify="right")
    table.add_column("Floors %", justify="right")
    table.add_column("Units %", justify="right")
    table.add_column("Height %", justify="right")

    for item in report.files:
        completeness = {fc.field_name: fc.completeness_pct for fc in item.field_completeness}
        table.add_row(
            item.file_name,
            item.province_territory,
            f"{item.total_records:,}",
            f"{item.file_size_mb:.1f}",
            str(len(item.source_organizations)),
            f"{completeness.get('type', 0):.1f}",
            f"{completeness.get('floors', 0):.1f}",
            f"{completeness.get('units', 0):.1f}",
            f"{completeness.get('height', 0):.1f}",
        )

    table.add_section()
    table.add_row(
        "[bold]TOTAL[/bold]",
        "",
        f"[bold]{report.total_records:,}[/bold]",
        f"[bold]{report.total_size_mb:.1f}[/bold]",
        "",
        "",
        "",
        "",
        "",
    )

    console.print(table)
    console.print(f"\n[green]Inventory saved to:[/green] {output_path}")


@app.command()
def audit_schema(
    config: str = typer.Option("config/default.yaml", help="Configuration file path"),
    data_dir: str | None = typer.Option(None, help="Override data directory"),
) -> None:
    """Audit every GeoPackage: field frequencies, numeric parsing, source completeness, geometry quality."""
    from murb_geometry.ingestion.schema_audit import run_schema_audit

    cfg = load_config(config_path=config, local_path="config/local.yaml")
    root = Path(data_dir) if data_dir else cfg.paths.data_dir

    console.print(f"[bold]Schema audit:[/bold] {root} (full population, no row caps)")
    manifest = run_schema_audit(data_dir=root)

    console.print(f"\n[green]Audit complete:[/green] {manifest['files_audited']} files")
    console.print(f"  Time: {manifest['total_audit_seconds']:.1f}s")
    for f in manifest.get("output_files", []):
        console.print(f"  outputs/reports/{f}")


@app.command()
def inspect(
    file: str = typer.Argument(..., help="Path to a GeoPackage file"),
    layer: str | None = typer.Option(None, help="Layer name (auto-detected if omitted)"),
) -> None:
    """Inspect schema, CRS, row count, and completeness of a GeoPackage file."""
    from murb_geometry.ingestion.inventory import inspect_geopackage

    gpkg_path = Path(file)
    if not gpkg_path.exists():
        console.print(f"[red]File not found:[/red] {file}")
        raise typer.Exit(code=1)

    console.print(f"[bold]Inspecting:[/bold] {gpkg_path.name}")
    item = inspect_geopackage(gpkg_path)

    for ly in item.layers:
        console.print(f"\n[bold cyan]Layer:[/bold cyan] {ly.layer_name}")
        console.print(f"  Geometry type: {ly.geometry_type}")
        console.print(f"  CRS (EPSG):    {ly.crs_epsg}")
        console.print(f"  Row count:     {ly.row_count:,}")
        console.print(f"  Fields ({ly.field_count}):  {', '.join(ly.fields)}")

    if item.field_completeness:
        table = Table(title="Field Completeness")
        table.add_column("Field")
        table.add_column("Non-Missing", justify="right")
        table.add_column("Completeness", justify="right")
        table.add_column("Distinct Values", justify="right")
        for fc in item.field_completeness:
            style = (
                "green"
                if fc.completeness_pct > 50
                else ("yellow" if fc.completeness_pct > 10 else "red")
            )
            table.add_row(
                fc.field_name,
                f"{fc.non_missing_count:,}",
                f"[{style}]{fc.completeness_pct:.1f}%[/{style}]",
                f"{fc.distinct_count:,}" if fc.distinct_count else "-",
            )
        console.print(table)

    if item.source_organizations:
        console.print(f"\n[bold]Source organizations ({len(item.source_organizations)}):[/bold]")
        for src in item.source_organizations[:20]:
            console.print(f"  • {src}")
        if len(item.source_organizations) > 20:
            console.print(f"  ... and {len(item.source_organizations) - 20} more")


@app.command()
def validate(
    config: str = typer.Option("config/default.yaml", help="Configuration file path"),
    province: str | None = typer.Option(None, help="Province filter (e.g., 'NS')"),
) -> None:
    """Validate geometries and flag quality issues."""
    import geopandas as gpd

    from murb_geometry.ingestion.inventory import discover_geopackages
    from murb_geometry.validation.geometry import validate_geometry

    cfg = load_config(config_path=config, local_path="config/local.yaml")
    gpkg_files = discover_geopackages(cfg.paths.data_dir)

    for gpkg_path in gpkg_files:
        prov = gpkg_path.stem.replace("ODB_v3_", "").split("_")[0]
        if province and prov.upper() != province.upper():
            continue
        console.print(f"[bold]Validating:[/bold] {gpkg_path.name}")
        gdf = gpd.read_file(gpkg_path, rows=100)
        valid_count = sum(1 for g in gdf.geometry if validate_geometry(g)["is_valid"])
        console.print(f"  Sample: {valid_count}/{len(gdf)} valid geometries")


@app.command()
def normalize(
    config: str = typer.Option("config/default.yaml", help="Configuration file path"),
    province: str | None = typer.Option(None, help="Province filter"),
) -> None:
    """Normalize source-specific schemas to a common data model."""
    console.print(
        "[yellow]Use the Python API:[/yellow]\n"
        "  from murb_geometry.classification import normalize_type_value"
    )


@app.command()
def classify(
    config: str = typer.Option("config/default.yaml", help="Configuration file path"),
    province: str | None = typer.Option(None, help="Province filter"),
) -> None:
    """Classify buildings as candidate MURBs with confidence scores."""
    import geopandas as gpd

    from murb_geometry.classification.classifier import classify_building, normalize_type_value
    from murb_geometry.ingestion.inventory import discover_geopackages

    cfg = load_config(config_path=config, local_path="config/local.yaml")
    gpkg_files = discover_geopackages(cfg.paths.data_dir)

    for gpkg_path in gpkg_files:
        prov = gpkg_path.stem.replace("ODB_v3_", "").split("_")[0]
        if province and prov.upper() != province.upper():
            continue
        console.print(f"[bold]Classifying:[/bold] {gpkg_path.name}")
        gdf = gpd.read_file(gpkg_path, rows=500)
        results: dict[str, int] = {}
        for _, row in gdf.iterrows():
            type_norm = normalize_type_value(row.get("type"))
            units_str = row.get("units")
            units_num = int(units_str) if units_str and units_str != ".." else None
            result = classify_building(type_normalized=type_norm, units_numeric=units_num)
            results[result.confidence_level] = results.get(result.confidence_level, 0) + 1
        for level, count in sorted(results.items(), key=lambda x: -x[1]):
            console.print(f"  {level}: {count}")


@app.command()
def metrics(
    config: str = typer.Option("config/default.yaml", help="Configuration file path"),
    province: str | None = typer.Option(None, help="Province filter"),
    sample: int = typer.Option(100, help="Number of records to sample"),
) -> None:
    """Calculate geometry metrics (area, dimensions, aspect ratio, shape)."""
    import geopandas as gpd

    from murb_geometry.geometry.metrics import compute_geometry_metrics
    from murb_geometry.ingestion.inventory import discover_geopackages
    from murb_geometry.statistics.descriptive import compute_descriptive_stats

    cfg = load_config(config_path=config, local_path="config/local.yaml")
    gpkg_files = discover_geopackages(cfg.paths.data_dir)

    for gpkg_path in gpkg_files:
        prov = gpkg_path.stem.replace("ODB_v3_", "").split("_")[0]
        if province and prov.upper() != province.upper():
            continue
        console.print(f"[bold]Computing metrics:[/bold] {gpkg_path.name} (sample={sample})")
        gdf = gpd.read_file(gpkg_path, rows=sample)
        areas: list[float] = []
        for geom in gdf.geometry:
            m = compute_geometry_metrics(geom)
            areas.append(m["footprint_area_m2"])
        stats = compute_descriptive_stats(areas, field_name="footprint_area_m2")
        console.print(
            f"  Records: {stats['count']}, "
            f"Area — min: {stats['min']:.0f}, median: {stats['median']:.0f}, "
            f"max: {stats['max']:.0f}, mean: {stats['mean']:.0f} m2"
        )


@app.command()
def enrich(
    config: str = typer.Option("config/default.yaml", help="Configuration file path"),
    source: str | None = typer.Option(None, help="Enrichment source"),
) -> None:
    """Enrich building records with external authoritative data."""
    console.print(
        "[yellow]Enrichment requires external data sources.[/yellow]\n"
        "  from murb_geometry.enrichment import EnrichmentSource, apply_enrichment"
    )


@app.command()
def summarize(
    config: str = typer.Option("config/default.yaml", help="Configuration file path"),
    province: str | None = typer.Option(None, help="Province filter"),
    output: str | None = typer.Option(None, help="Output JSON path"),
) -> None:
    """Generate descriptive statistics and summaries."""
    import json

    import geopandas as gpd

    from murb_geometry.geometry.metrics import compute_geometry_metrics
    from murb_geometry.ingestion.inventory import discover_geopackages
    from murb_geometry.statistics.descriptive import compute_descriptive_stats

    cfg = load_config(config_path=config, local_path="config/local.yaml")
    gpkg_files = discover_geopackages(cfg.paths.data_dir)
    output_path = Path(output) if output else Path("outputs/reports/summary.json")

    all_areas: list[float] = []
    all_aspect: list[float] = []

    for gpkg_path in gpkg_files:
        prov = gpkg_path.stem.replace("ODB_v3_", "").split("_")[0]
        if province and prov.upper() != province.upper():
            continue
        console.print(f"[bold]Summarizing:[/bold] {gpkg_path.name} (sample=200)")
        gdf = gpd.read_file(gpkg_path, rows=200)
        for geom in gdf.geometry:
            m = compute_geometry_metrics(geom)
            all_areas.append(m["footprint_area_m2"])
            all_aspect.append(m["aspect_ratio"])

    results = [
        compute_descriptive_stats(all_areas, "footprint_area_m2"),
        compute_descriptive_stats(all_aspect, "aspect_ratio"),
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    console.print(f"[green]Summary saved to:[/green] {output_path}")


@app.command()
def archetypes(
    config: str = typer.Option("config/default.yaml", help="Configuration file path"),
    method: str = typer.Option("medoid", help="Archetype method"),
) -> None:
    """Derive representative MURB archetypes."""
    console.print(
        "[yellow]Archetype derivation requires classified data.[/yellow]\n"
        "  from murb_geometry.archetypes import select_medoid"
    )


@app.command()
def excel(
    config: str = typer.Option("config/default.yaml", help="Configuration file path"),
    output: str | None = typer.Option(None, help="Output workbook path"),
) -> None:
    """Generate formatted Excel workbook report."""
    import json

    from murb_geometry.excel.workbook import create_summary_workbook

    output_path = Path(output) if output else Path("outputs/excel/murb_report.xlsx")
    inv_path = Path("outputs/reports/inventory.json")

    if not inv_path.exists():
        console.print("[red]No inventory found.[/red] Run 'murb-geometry inventory' first.")
        raise typer.Exit(code=1)

    inv = json.loads(inv_path.read_text())
    completeness: list[dict[str, object]] = []
    for f in inv["files"]:
        row: dict[str, object] = {
            "province": f["province_territory"],
            "records": f["total_records"],
        }
        for fc in f["field_completeness"]:
            row[fc["field_name"] + "_pct"] = fc["completeness_pct"]
        completeness.append(row)

    summary_path = Path("outputs/reports/summary.json")
    summary_stats = None
    if summary_path.exists():
        summary_stats = json.loads(summary_path.read_text())

    create_summary_workbook(
        output_path,
        completeness_data=completeness,
        summary_stats=summary_stats,
        metadata={"Source": "ODB v3", "Generated by": "murb-geometry excel"},
    )
    console.print(f"[green]Excel report saved to:[/green] {output_path}")


@app.command(name="excel-audit")
def excel_audit(
    output: str | None = typer.Option(None, help="Output workbook path"),
) -> None:
    """Generate the building-level audit Excel workbook from persisted MURB subsets."""
    from murb_geometry import datastore
    from murb_geometry.excel.building_audit import create_building_audit_workbook

    if not (datastore.subset_available("tiered") or datastore.subset_available("precision")):
        console.print(
            "[red]No processed MURB subsets found.[/red] Run 'murb-geometry run-all' first."
        )
        raise typer.Exit(code=1)

    output_path = Path(output) if output else Path("outputs/excel/murb_building_audit.xlsx")
    create_building_audit_workbook(output_path)
    console.print(f"[green]Building audit workbook saved to:[/green] {output_path}")


@app.command()
def visualize() -> None:
    """Launch the Streamlit visualization application."""
    import subprocess
    import sys

    console.print("[bold]Launching Streamlit...[/bold]")
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app/streamlit_app.py"])


@app.command()
def figures(
    output: str | None = typer.Option(None, help="Figures output directory"),
) -> None:
    """Regenerate publication figures from persisted run outputs (manifest + MURB subsets)."""
    from murb_geometry.visualization.charts import build_all_figures

    out = Path(output) if output else None
    try:
        written = build_all_figures(output_dir=out)
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    console.print(f"[green]Wrote {len(written)} figures[/green] to outputs/figures/")


@app.command()
def report() -> None:
    """Generate the direct RQ1-RQ10 research report from persisted pipeline outputs."""
    from pathlib import Path

    manifest_path = Path("outputs/reports/run_manifest.json")
    if not manifest_path.exists():
        console.print("[red]No pipeline outputs found.[/red] Run 'murb-geometry run-all' first.")
        raise typer.Exit(code=1)

    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "scripts/generate_research_report.py"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        console.print(
            "[green]Research report generated:[/green] outputs/reports/research_report.md"
        )
    else:
        console.print(f"[red]Report generation failed:[/red] {result.stderr}")
        raise typer.Exit(code=1)


@app.command()
def run_all(
    config: str = typer.Option("config/default.yaml", help="Configuration file path"),
    provinces: str | None = typer.Option(
        None, help="Comma-separated province codes (default: all)"
    ),
    output_dir: str | None = typer.Option(None, help="Output directory override"),
) -> None:
    """Execute the complete multi-pathway pipeline on all provinces.

    Processes the full eligible population without arbitrary row caps.
    Implements Option C — Multi-pathway reporting:
      1. Precision pathway (confirmed + high-confidence only)
      2. Tiered pathway (confirmed + high + probable + possible)

    Produces: GeoParquet, classification reports, sensitivity analysis,
    statistics, and run manifest.
    """
    from murb_geometry.pipeline import run_full_pipeline

    province_list = [p.strip().upper() for p in provinces.split(",")] if provinces else None
    out = Path(output_dir) if output_dir else None

    console.print("[bold]Starting full multi-pathway pipeline...[/bold]")
    if province_list:
        console.print(f"  Provinces: {', '.join(province_list)}")
    else:
        console.print("  Provinces: ALL (12 provinces/territories, 15 files)")
    console.print("  Pathway: Option C — Multi-pathway reporting")
    console.print("  Row limits: NONE (full population)")
    console.print()

    manifest = run_full_pipeline(
        config_path=config,
        provinces=province_list,
        output_dir=out,
    )

    # Display results
    totals = manifest.get("stages", {}).get("national_totals", {})
    console.print("\n[bold green]Pipeline complete![/bold green]")
    console.print(f"  Precision pathway: {totals.get('precision_buildings', 0):,} buildings")
    console.print(f"  Tiered pathway:    {totals.get('tiered_buildings', 0):,} buildings")
    console.print("  Manifest: outputs/reports/run_manifest.json")


@app.command(name="data-status")
def data_status(
    config: str = typer.Option("config/default.yaml", help="Configuration file path"),
) -> None:
    """Show availability and validity of the persisted MURB subsets.

    Downstream work (excel, report, archetypes, visualize) loads these subsets for
    fast processing. A subset is 'valid' when its provenance matches the current
    classification configuration; otherwise re-run 'murb-geometry run-all'.
    """
    from murb_geometry import datastore

    cfg = load_config(config_path=config, local_path="config/local.yaml")
    expected = datastore.build_classification_provenance(cfg)
    status = datastore.subset_status(expected_provenance=expected)

    console.print("[bold]Processed MURB subsets[/bold] (data/processed/):")
    for pathway, s in status.items():
        if not s["available"]:
            console.print(
                f"  [yellow]{pathway}[/yellow]: not produced — run 'murb-geometry run-all'"
            )
            continue
        rows = s["n_rows"]
        rows_str = f"{rows:,}" if isinstance(rows, int) else "?"
        tag = "[green]valid[/green]" if s["valid"] else "[red]STALE[/red]"
        console.print(
            f"  [bold]{pathway}[/bold]: {tag}  rows={rows_str}  "
            f"provinces={len(s['provinces'] or [])}  created={s['created_at']}"
        )
        if not s["valid"]:
            console.print(f"      reasons: {', '.join(s['invalid_reasons'])}")


@app.command()
def preprocess(
    config: str = typer.Option("config/default.yaml", help="Configuration file path"),
    province: str | None = typer.Option(None, help="Province filter"),
    pathway: str = typer.Option("tiered", help="Classification pathway: 'precision' or 'tiered'"),
) -> None:
    """Preprocess, classify, and compute metrics for a single province.

    Full population — no row caps. Results saved to data/processed/.
    """
    from murb_geometry.pipeline import PROVINCE_FILES, process_province

    cfg = load_config(config_path=config, local_path="config/local.yaml")

    if province:
        prov = province.upper()
        if prov not in PROVINCE_FILES:
            console.print(f"[red]Unknown province: {prov}[/red]")
            console.print(f"  Available: {', '.join(sorted(PROVINCE_FILES.keys()))}")
            raise typer.Exit(code=1)
        provinces_to_run = {prov: PROVINCE_FILES[prov]}
    else:
        provinces_to_run = PROVINCE_FILES

    for prov, files in provinces_to_run.items():
        console.print(f"[bold]Processing {prov}[/bold] ({len(files)} file(s), full population)...")
        result = process_province(prov, files, cfg)
        console.print(
            f"  Total: {result.get('total_records', 0):,}, "
            f"Precision: {result.get('precision_count', 0):,}, "
            f"Tiered: {result.get('tiered_count', 0):,} "
            f"({result.get('timing_seconds', 0):.1f}s)"
        )


@app.command()
def gbxml(
    config: str = typer.Option("config/default.yaml", help="Configuration file path"),
    building_id: str | None = typer.Option(None, help="Specific building ID to export"),
    archetype_id: str | None = typer.Option(None, help="Archetype ID to export"),
    output: str | None = typer.Option(None, help="Output gbXML path"),
) -> None:
    """Generate gbXML files for simulation."""
    console.print(
        "[yellow]gbXML export requires a populated BuildingGeometryModel.[/yellow]\n"
        "  from murb_geometry.gbxml import BuildingGeometryModel, Storey, Surface"
    )


@app.command()
def run(
    config: str = typer.Option("config/default.yaml", help="Configuration file path"),
    dry_run: bool = typer.Option(False, help="Show what would be done without executing"),
) -> None:
    """Execute the complete analytical workflow."""
    import json

    import geopandas as gpd

    from murb_geometry.excel.workbook import create_summary_workbook
    from murb_geometry.geometry.metrics import compute_geometry_metrics
    from murb_geometry.ingestion.inventory import discover_geopackages, run_inventory
    from murb_geometry.statistics.descriptive import compute_descriptive_stats

    cfg = load_config(config_path=config, local_path="config/local.yaml")

    if dry_run:
        console.print("[bold]Dry run — would execute:[/bold]")
        console.print("  1. Inventory all GeoPackage files")
        console.print("  2. Compute geometry metrics (sampled)")
        console.print("  3. Generate Excel report")
        return

    console.print("[bold]Running full pipeline...[/bold]")

    # Step 1: Inventory
    console.print("\n[cyan]Step 1: Inventory[/cyan]")
    report = run_inventory(
        data_dir=cfg.paths.data_dir,
        output_path=Path("outputs/reports/inventory.json"),
        missing_markers=cfg.input.missing_value_markers,
        compute_hashes=False,
    )
    console.print(f"  {report.total_files} files, {report.total_records:,} records")

    # Step 2: Summarize (sampled)
    console.print("\n[cyan]Step 2: Geometry summary (sampled)[/cyan]")
    all_areas: list[float] = []
    for gpkg_path in discover_geopackages(cfg.paths.data_dir):
        gdf = gpd.read_file(gpkg_path, rows=50)
        for geom in gdf.geometry:
            m = compute_geometry_metrics(geom)
            all_areas.append(m["footprint_area_m2"])
    summary = [compute_descriptive_stats(all_areas, "footprint_area_m2")]
    Path("outputs/reports").mkdir(parents=True, exist_ok=True)
    with open("outputs/reports/summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)
    console.print(f"  {len(all_areas)} buildings sampled")

    # Step 3: Excel
    console.print("\n[cyan]Step 3: Excel report[/cyan]")
    inv = json.loads(Path("outputs/reports/inventory.json").read_text())
    completeness: list[dict[str, object]] = []
    for fi in inv["files"]:
        row: dict[str, object] = {
            "province": fi["province_territory"],
            "records": fi["total_records"],
        }
        for fc in fi["field_completeness"]:
            row[fc["field_name"] + "_pct"] = fc["completeness_pct"]
        completeness.append(row)
    create_summary_workbook(
        Path("outputs/excel/murb_report.xlsx"),
        completeness_data=completeness,
        summary_stats=summary,
        metadata={"Source": "ODB v3", "Generated by": "murb-geometry run"},
    )
    console.print("  outputs/excel/murb_report.xlsx")
    console.print("\n[bold green]Pipeline complete![/bold green]")


if __name__ == "__main__":
    app()
