"""Unit tests for the ingestion/inventory module."""

import sqlite3
from pathlib import Path

import pytest

from murb_geometry.ingestion.inventory import (
    GeoPackageInventoryItem,
    InventoryReport,
    discover_geopackages,
    inspect_geopackage,
    run_inventory,
)


@pytest.fixture
def sample_gpkg(tmp_path: Path) -> Path:
    """Create a minimal GeoPackage for testing."""
    gpkg_path = tmp_path / "ODB_v3_TEST.gpkg"
    conn = sqlite3.connect(gpkg_path)
    cur = conn.cursor()

    # Create GeoPackage metadata tables
    cur.execute("""
        CREATE TABLE gpkg_contents (
            table_name TEXT NOT NULL PRIMARY KEY,
            data_type TEXT NOT NULL,
            identifier TEXT,
            description TEXT,
            last_change TEXT,
            min_x REAL,
            min_y REAL,
            max_x REAL,
            max_y REAL,
            srs_id INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE gpkg_geometry_columns (
            table_name TEXT NOT NULL,
            column_name TEXT NOT NULL,
            geometry_type_name TEXT NOT NULL,
            srs_id INTEGER NOT NULL,
            z INTEGER NOT NULL,
            m INTEGER NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE gpkg_spatial_ref_sys (
            srs_name TEXT NOT NULL,
            srs_id INTEGER NOT NULL PRIMARY KEY,
            organization TEXT NOT NULL,
            organization_coordsys_id INTEGER NOT NULL,
            definition TEXT NOT NULL,
            description TEXT
        )
    """)

    # Add CRS definition
    cur.execute("""
        INSERT INTO gpkg_spatial_ref_sys
        VALUES ('NAD83 / Statistics Canada Lambert', 3347, 'EPSG', 3347, '', '')
    """)

    # Create data layer
    cur.execute("""
        CREATE TABLE ODB_v3_TEST (
            fid INTEGER PRIMARY KEY AUTOINCREMENT,
            geom BLOB,
            id TEXT,
            source_id TEXT,
            source TEXT,
            dataset TEXT,
            csduid TEXT,
            csdname TEXT,
            prov_terr TEXT,
            name TEXT,
            type TEXT,
            address TEXT,
            year_built TEXT,
            units TEXT,
            floors TEXT,
            sq_ft TEXT,
            height TEXT
        )
    """)

    # Register in gpkg_contents
    cur.execute("""
        INSERT INTO gpkg_contents (table_name, data_type, srs_id)
        VALUES ('ODB_v3_TEST', 'features', 3347)
    """)
    cur.execute("""
        INSERT INTO gpkg_geometry_columns (table_name, column_name, geometry_type_name, srs_id, z, m)
        VALUES ('ODB_v3_TEST', 'geom', 'POLYGON', 3347, 0, 0)
    """)

    # Insert sample records
    records = [
        (
            "id1",
            "sid1",
            "City of Test",
            "Buildings",
            "1001001",
            "Testville",
            "TS",
            "..",
            "Residential",
            "123 Main St",
            "2000",
            "12",
            "4",
            "..",
            "15",
        ),
        (
            "id2",
            "sid2",
            "City of Test",
            "Buildings",
            "1001001",
            "Testville",
            "TS",
            "..",
            "Commercial",
            "456 Oak Ave",
            "..",
            "..",
            "2",
            "..",
            "..",
        ),
        (
            "id3",
            "sid3",
            "Government of Canada",
            "Auto Extract",
            "1001002",
            "Othertown",
            "TS",
            "..",
            "..",
            "..",
            "..",
            "..",
            "..",
            "..",
            "..",
        ),
        (
            "id4",
            "sid4",
            "City of Test",
            "Buildings",
            "1001001",
            "Testville",
            "TS",
            "..",
            "Residential",
            "789 Elm St",
            "1990",
            "6",
            "..",
            "500",
            "..",
        ),
        (
            "id5",
            "sid5",
            "Government of Canada",
            "Auto Extract",
            "1001002",
            "Othertown",
            "TS",
            "..",
            "..",
            "..",
            "..",
            "..",
            "..",
            "..",
            "..",
        ),
    ]
    for r in records:
        cur.execute(
            "INSERT INTO ODB_v3_TEST "
            "(geom, id, source_id, source, dataset, csduid, csdname, prov_terr, "
            "name, type, address, year_built, units, floors, sq_ft, height) "
            "VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            r,
        )

    conn.commit()
    conn.close()

    # Set GeoPackage magic bytes to suppress pyogrio warnings
    import struct

    with open(gpkg_path, "r+b") as f:
        f.seek(68)
        f.write(struct.pack(">I", 0x47504B47))  # application_id = 'GPKG'
        f.seek(96)
        f.write(struct.pack(">I", 10300))  # user_version = 1.3.0

    return gpkg_path


def test_discover_geopackages(sample_gpkg: Path) -> None:
    """discover_geopackages finds .gpkg files recursively."""
    results = discover_geopackages(sample_gpkg.parent)
    assert len(results) == 1
    assert results[0] == sample_gpkg


def test_discover_geopackages_empty(tmp_path: Path) -> None:
    """discover_geopackages returns empty list for directory with no .gpkg."""
    results = discover_geopackages(tmp_path)
    assert results == []


def test_inspect_geopackage_basic(sample_gpkg: Path) -> None:
    """inspect_geopackage returns correct metadata."""
    item = inspect_geopackage(sample_gpkg, compute_hash=False)
    assert isinstance(item, GeoPackageInventoryItem)
    assert item.file_name == "ODB_v3_TEST.gpkg"
    assert item.province_territory == "TEST"
    assert item.total_records == 5
    assert len(item.layers) == 1
    assert item.layers[0].layer_name == "ODB_v3_TEST"
    assert item.layers[0].geometry_type == "POLYGON"
    assert item.layers[0].crs_epsg == 3347
    assert item.layers[0].row_count == 5


def test_inspect_geopackage_completeness(sample_gpkg: Path) -> None:
    """inspect_geopackage calculates field completeness correctly."""
    item = inspect_geopackage(sample_gpkg, compute_hash=False)
    completeness = {fc.field_name: fc for fc in item.field_completeness}

    # 'type' field: 3 out of 5 are non-missing (Residential, Commercial, Residential)
    assert completeness["type"].non_missing_count == 3
    assert completeness["type"].completeness_pct == 60.0

    # 'floors' field: 2 out of 5 have values (4, 2)
    assert completeness["floors"].non_missing_count == 2
    assert completeness["floors"].completeness_pct == 40.0

    # 'units' field: 2 out of 5 have values (12, 6)
    assert completeness["units"].non_missing_count == 2
    assert completeness["units"].completeness_pct == 40.0


def test_inspect_geopackage_sources(sample_gpkg: Path) -> None:
    """inspect_geopackage identifies source organizations."""
    item = inspect_geopackage(sample_gpkg, compute_hash=False)
    assert "City of Test" in item.source_organizations
    assert "Government of Canada" in item.source_organizations
    assert len(item.source_organizations) == 2


def test_inspect_geopackage_hash(sample_gpkg: Path) -> None:
    """inspect_geopackage computes file hash when requested."""
    item = inspect_geopackage(sample_gpkg, compute_hash=True)
    assert len(item.sha256_hash) == 64  # SHA-256 hex length


def test_run_inventory(sample_gpkg: Path) -> None:
    """run_inventory produces a complete report."""
    output_path = sample_gpkg.parent / "inventory.json"
    report = run_inventory(
        data_dir=sample_gpkg.parent,
        output_path=output_path,
        compute_hashes=False,
    )
    assert isinstance(report, InventoryReport)
    assert report.total_files == 1
    assert report.total_records == 5
    assert output_path.exists()


def test_run_inventory_writes_json(sample_gpkg: Path) -> None:
    """run_inventory writes valid JSON."""
    import json

    output_path = sample_gpkg.parent / "report.json"
    run_inventory(data_dir=sample_gpkg.parent, output_path=output_path, compute_hashes=False)

    with open(output_path) as f:
        data = json.load(f)

    assert data["total_files"] == 1
    assert data["total_records"] == 5
    assert len(data["files"]) == 1
    assert data["files"][0]["province_territory"] == "TEST"
