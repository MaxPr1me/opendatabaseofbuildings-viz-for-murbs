"""GeoPackage inventory — discovery, inspection, and completeness reporting.

Implements efficient GeoPackage inspection using sqlite3 (no heavy geospatial
libraries required) for metadata operations, and pyogrio for schema/CRS details.
"""

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pyogrio
from pydantic import BaseModel, Field

from murb_geometry import __version__


class FieldCompleteness(BaseModel):
    """Completeness statistics for a single field."""

    field_name: str
    total_records: int
    non_missing_count: int
    missing_count: int
    completeness_pct: float
    distinct_count: int | None = None


class LayerInfo(BaseModel):
    """Metadata for a single GeoPackage layer."""

    layer_name: str
    geometry_type: str
    crs_epsg: int | None = None
    crs_wkt: str | None = None
    row_count: int
    field_count: int
    fields: list[str] = Field(default_factory=list)
    field_types: dict[str, str] = Field(default_factory=dict)


class GeoPackageInventoryItem(BaseModel):
    """Complete inventory record for one GeoPackage file."""

    file_path: str
    file_name: str
    file_size_bytes: int
    file_size_mb: float
    sha256_hash: str
    province_territory: str
    layers: list[LayerInfo] = Field(default_factory=list)
    total_records: int = 0
    source_organizations: list[str] = Field(default_factory=list)
    field_completeness: list[FieldCompleteness] = Field(default_factory=list)
    inspection_timestamp: str = ""


class InventoryReport(BaseModel):
    """Complete national inventory report."""

    generated_at: str
    software_version: str
    data_directory: str
    total_files: int
    total_records: int
    total_size_mb: float
    files: list[GeoPackageInventoryItem] = Field(default_factory=list)


def discover_geopackages(data_dir: Path) -> list[Path]:
    """Discover all GeoPackage files recursively under data_dir.

    Parameters
    ----------
    data_dir
        Root directory to search for .gpkg files.

    Returns
    -------
    list[Path]
        Sorted list of discovered GeoPackage file paths.
    """
    return sorted(data_dir.rglob("*.gpkg"))


def _compute_file_hash(path: Path, algorithm: str = "sha256") -> str:
    """Compute file hash without loading entire file into memory."""
    h = hashlib.new(algorithm)
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def _get_layer_info_sqlite(gpkg_path: Path) -> list[dict[str, Any]]:
    """Extract layer metadata using sqlite3 (fast, no GDAL required)."""
    conn = sqlite3.connect(gpkg_path)
    cur = conn.cursor()

    layers = []
    cur.execute("SELECT table_name, data_type, srs_id FROM gpkg_contents")
    for table_name, data_type, srs_id in cur.fetchall():
        if data_type != "features":
            continue

        # Get geometry info
        cur.execute(
            "SELECT column_name, geometry_type_name, srs_id "
            "FROM gpkg_geometry_columns WHERE table_name = ?",
            (table_name,),
        )
        geom_row = cur.fetchone()
        geom_type = geom_row[1] if geom_row else "UNKNOWN"

        # Get row count
        cur.execute(f"SELECT COUNT(*) FROM [{table_name}]")
        row_count = cur.fetchone()[0]

        # Get column info
        cur.execute(f"PRAGMA table_info([{table_name}])")
        columns = cur.fetchall()
        field_names = [c[1] for c in columns]
        field_types = {c[1]: c[2] for c in columns}

        layers.append(
            {
                "layer_name": table_name,
                "geometry_type": geom_type,
                "srs_id": srs_id,
                "row_count": row_count,
                "field_count": len(field_names),
                "fields": field_names,
                "field_types": field_types,
            }
        )

    conn.close()
    return layers


def _get_field_completeness(
    gpkg_path: Path,
    layer_name: str,
    missing_markers: list[str],
) -> list[FieldCompleteness]:
    """Calculate field completeness using sqlite3 for efficiency."""
    conn = sqlite3.connect(gpkg_path)
    cur = conn.cursor()

    cur.execute(f"SELECT COUNT(*) FROM [{layer_name}]")
    total = cur.fetchone()[0]

    # Get text attribute fields (skip fid and geom)
    cur.execute(f"PRAGMA table_info([{layer_name}])")
    columns = cur.fetchall()
    text_fields = [c[1] for c in columns if c[2] == "TEXT"]

    results = []
    for field in text_fields:
        # Build condition for missing values
        conditions = [f"[{field}] IS NULL"]
        for marker in missing_markers:
            conditions.append(f"[{field}] = '{marker}'")
        where_clause = " OR ".join(conditions)

        cur.execute(f"SELECT COUNT(*) FROM [{layer_name}] WHERE NOT ({where_clause})")
        non_missing = cur.fetchone()[0]

        # Get distinct count (sample for performance on large files)
        cur.execute(
            f"SELECT COUNT(DISTINCT [{field}]) FROM [{layer_name}] WHERE NOT ({where_clause})"
        )
        distinct_count = cur.fetchone()[0]

        results.append(
            FieldCompleteness(
                field_name=field,
                total_records=total,
                non_missing_count=non_missing,
                missing_count=total - non_missing,
                completeness_pct=round(100.0 * non_missing / total, 2) if total > 0 else 0.0,
                distinct_count=distinct_count,
            )
        )

    conn.close()
    return results


def _get_source_organizations(gpkg_path: Path, layer_name: str) -> list[str]:
    """Get distinct source organizations from a GeoPackage layer."""
    conn = sqlite3.connect(gpkg_path)
    cur = conn.cursor()
    cur.execute(
        f"SELECT DISTINCT source FROM [{layer_name}] "
        "WHERE source IS NOT NULL AND source != '..' ORDER BY source"
    )
    sources = [row[0] for row in cur.fetchall()]
    conn.close()
    return sources


def inspect_geopackage(
    gpkg_path: Path,
    missing_markers: list[str] | None = None,
    compute_hash: bool = True,
) -> GeoPackageInventoryItem:
    """Inspect a single GeoPackage file and return its inventory record.

    Parameters
    ----------
    gpkg_path
        Path to the GeoPackage file.
    missing_markers
        Values to treat as missing (default: ["..", "", "NA", "N/A"]).
    compute_hash
        Whether to compute SHA-256 hash (can be slow for large files).

    Returns
    -------
    GeoPackageInventoryItem
        Complete inventory record for the file.
    """
    if missing_markers is None:
        missing_markers = ["..", "", "NA", "N/A"]

    file_size = gpkg_path.stat().st_size
    file_hash = _compute_file_hash(gpkg_path) if compute_hash else ""

    # Extract province from filename (e.g., ODB_v3_NS.gpkg -> NS)
    stem = gpkg_path.stem
    province = stem.replace("ODB_v3_", "").split("_")[0] if "ODB_v3_" in stem else ""

    # Get layer info
    raw_layers = _get_layer_info_sqlite(gpkg_path)

    # Get CRS via pyogrio for proper EPSG identification
    layers: list[LayerInfo] = []
    for raw in raw_layers:
        try:
            info = pyogrio.read_info(gpkg_path, layer=raw["layer_name"])
            crs_wkt = info.get("crs", "")
            # Extract EPSG from CRS
            crs_epsg = raw["srs_id"]
        except Exception:
            crs_wkt = None
            crs_epsg = raw["srs_id"]

        layers.append(
            LayerInfo(
                layer_name=raw["layer_name"],
                geometry_type=raw["geometry_type"],
                crs_epsg=crs_epsg,
                crs_wkt=crs_wkt if isinstance(crs_wkt, str) else None,
                row_count=raw["row_count"],
                field_count=raw["field_count"],
                fields=raw["fields"],
                field_types=raw["field_types"],
            )
        )

    # Get completeness for first (primary) layer
    completeness: list[FieldCompleteness] = []
    sources: list[str] = []
    total_records = 0
    if layers:
        primary = layers[0]
        total_records = primary.row_count
        completeness = _get_field_completeness(gpkg_path, primary.layer_name, missing_markers)
        sources = _get_source_organizations(gpkg_path, primary.layer_name)

    return GeoPackageInventoryItem(
        file_path=str(gpkg_path),
        file_name=gpkg_path.name,
        file_size_bytes=file_size,
        file_size_mb=round(file_size / (1024 * 1024), 1),
        sha256_hash=file_hash,
        province_territory=province,
        layers=layers,
        total_records=total_records,
        source_organizations=sources,
        field_completeness=completeness,
        inspection_timestamp=datetime.now(UTC).isoformat(),
    )


def run_inventory(
    data_dir: Path,
    output_path: Path | None = None,
    missing_markers: list[str] | None = None,
    compute_hashes: bool = True,
) -> InventoryReport:
    """Run complete inventory of all GeoPackage files.

    Parameters
    ----------
    data_dir
        Root directory containing GeoPackage files.
    output_path
        Optional path to write JSON inventory report.
    missing_markers
        Values to treat as missing.
    compute_hashes
        Whether to compute file hashes.

    Returns
    -------
    InventoryReport
        Complete inventory report.
    """
    gpkg_files = discover_geopackages(data_dir)

    items: list[GeoPackageInventoryItem] = []
    for gpkg_path in gpkg_files:
        item = inspect_geopackage(
            gpkg_path,
            missing_markers=missing_markers,
            compute_hash=compute_hashes,
        )
        items.append(item)

    report = InventoryReport(
        generated_at=datetime.now(UTC).isoformat(),
        software_version=__version__,
        data_directory=str(data_dir),
        total_files=len(items),
        total_records=sum(i.total_records for i in items),
        total_size_mb=round(sum(i.file_size_mb for i in items), 1),
        files=items,
    )

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(report.model_dump(), f, indent=2)

    return report
