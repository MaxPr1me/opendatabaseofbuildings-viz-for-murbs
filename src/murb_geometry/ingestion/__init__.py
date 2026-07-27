"""Data ingestion module — GeoPackage discovery, reading, and inventory.

Provides functions to discover, inspect, and inventory GeoPackage files
from the Statistics Canada Open Database of Buildings.
"""

from murb_geometry.ingestion.inventory import (
    discover_geopackages,
    inspect_geopackage,
    run_inventory,
)

__all__ = ["discover_geopackages", "inspect_geopackage", "run_inventory"]
