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
    typer.echo("Command 'validate' is planned for Phase 2.")
    raise typer.Exit(code=0)


@app.command()
def normalize(
    config: str = typer.Option("config/default.yaml", help="Configuration file path"),
    province: str | None = typer.Option(None, help="Province filter"),
) -> None:
    """Normalize source-specific schemas to a common data model."""
    typer.echo("Command 'normalize' is planned for Phase 2.")
    raise typer.Exit(code=0)


@app.command()
def classify(
    config: str = typer.Option("config/default.yaml", help="Configuration file path"),
    province: str | None = typer.Option(None, help="Province filter"),
) -> None:
    """Classify buildings as candidate MURBs with confidence scores."""
    typer.echo("Command 'classify' is planned for Phase 3.")
    raise typer.Exit(code=0)


@app.command()
def metrics(
    config: str = typer.Option("config/default.yaml", help="Configuration file path"),
    province: str | None = typer.Option(None, help="Province filter"),
) -> None:
    """Calculate geometry metrics (area, dimensions, aspect ratio, shape)."""
    typer.echo("Command 'metrics' is planned for Phase 2.")
    raise typer.Exit(code=0)


@app.command()
def enrich(
    config: str = typer.Option("config/default.yaml", help="Configuration file path"),
    source: str | None = typer.Option(None, help="Enrichment source"),
) -> None:
    """Enrich building records with external authoritative data."""
    typer.echo("Command 'enrich' is planned for Phase 5.")
    raise typer.Exit(code=0)


@app.command()
def summarize(
    config: str = typer.Option("config/default.yaml", help="Configuration file path"),
    province: str | None = typer.Option(None, help="Province filter"),
    output: str | None = typer.Option(None, help="Output file path"),
) -> None:
    """Generate descriptive statistics and summaries."""
    typer.echo("Command 'summarize' is planned for Phase 4.")
    raise typer.Exit(code=0)


@app.command()
def archetypes(
    config: str = typer.Option("config/default.yaml", help="Configuration file path"),
    method: str = typer.Option("medoid", help="Archetype method"),
) -> None:
    """Derive representative MURB archetypes."""
    typer.echo("Command 'archetypes' is planned for Phase 6.")
    raise typer.Exit(code=0)


@app.command()
def excel(
    config: str = typer.Option("config/default.yaml", help="Configuration file path"),
    output: str | None = typer.Option(None, help="Output workbook path"),
) -> None:
    """Generate formatted Excel workbook report."""
    typer.echo("Command 'excel' is planned for Phase 4.")
    raise typer.Exit(code=0)


@app.command()
def visualize() -> None:
    """Launch the Streamlit visualization application."""
    typer.echo("Command 'visualize' is planned for Phase 4.")
    typer.echo("When implemented: streamlit run app/streamlit_app.py")
    raise typer.Exit(code=0)


@app.command()
def gbxml(
    config: str = typer.Option("config/default.yaml", help="Configuration file path"),
    building_id: str | None = typer.Option(None, help="Specific building ID to export"),
    archetype_id: str | None = typer.Option(None, help="Archetype ID to export"),
    output: str | None = typer.Option(None, help="Output gbXML path"),
) -> None:
    """Generate gbXML files for simulation."""
    typer.echo("Command 'gbxml' is planned for Phase 7.")
    raise typer.Exit(code=0)


@app.command()
def run(
    config: str = typer.Option("config/default.yaml", help="Configuration file path"),
    dry_run: bool = typer.Option(False, help="Show what would be done without executing"),
) -> None:
    """Execute the complete analytical workflow."""
    typer.echo("Command 'run' is planned for Phase 8.")
    raise typer.Exit(code=0)


if __name__ == "__main__":
    app()
