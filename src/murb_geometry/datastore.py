"""Processed MURB-subset data store.

After a full pipeline run, only the classified MURB subsets (precision and tiered)
are persisted to GeoParquet, each with a provenance manifest. Downstream work
(statistics, archetypes, Excel, visualisation, gbXML) loads these small subsets
instead of re-processing the ~14M-row national population.

The full-population run remains available via
:func:`murb_geometry.pipeline.run_full_pipeline`; this module only governs
persistence, retrieval, and validity of the MURB subset so cached data is reused
only when it matches the current classification configuration.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import geopandas as gpd

logger = logging.getLogger(__name__)

PATHWAYS: tuple[str, ...] = ("precision", "tiered")
_DEFAULT_PROCESSED_DIR = Path("data/processed")
_SUBSET_FILES: dict[str, str] = {
    "precision": "murbs_precision.parquet",
    "tiered": "murbs_tiered.parquet",
}


class ProcessedDataUnavailableError(RuntimeError):
    """Raised when a requested MURB subset has not been produced yet."""


def processed_dir(base: Path | None = None) -> Path:
    """Return the processed-data directory (default: data/processed)."""
    return base or _DEFAULT_PROCESSED_DIR


def subset_path(pathway: str, base: Path | None = None) -> Path:
    """Return the GeoParquet path for a pathway ('precision' or 'tiered')."""
    if pathway not in _SUBSET_FILES:
        msg = f"Unknown pathway '{pathway}'. Use one of {PATHWAYS}."
        raise ValueError(msg)
    return processed_dir(base) / _SUBSET_FILES[pathway]


def manifest_path(pathway: str, base: Path | None = None) -> Path:
    """Return the sidecar provenance-manifest path for a pathway."""
    return subset_path(pathway, base).with_suffix(".manifest.json")


def _file_sha256(path: Path) -> str | None:
    """SHA-256 of a file, or None if it does not exist."""
    if not path.exists():
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def build_classification_provenance(config: Any) -> dict[str, Any]:
    """Capture the classification inputs that define subset validity.

    Two subsets built with identical provenance are interchangeable; a change
    here (thresholds, type mapping, CRS) marks any cached subset stale.
    """
    mapping_file = Path(
        getattr(config.classification, "type_normalization_path", "config/type_normalization.yaml")
    )
    return {
        "classification": {
            "minimum_murb_units": config.classification.minimum_murb_units,
            "minimum_murb_storeys": config.classification.minimum_murb_storeys,
            "murb_height_threshold_m": config.classification.murb_height_threshold_m,
            "large_footprint_m2": config.classification.large_footprint_m2,
            "min_candidate_m2": config.classification.footprint_area["minimum_candidate_m2"],
        },
        "type_normalization_sha256": _file_sha256(mapping_file),
        "target_crs": config.input.target_projected_crs,
    }


def write_murb_subset(
    gdf: gpd.GeoDataFrame,
    pathway: str,
    *,
    base: Path | None = None,
    provenance: dict[str, Any] | None = None,
) -> Path:
    """Persist a MURB subset GeoParquet plus a provenance manifest.

    An empty subset writes no parquet but still records a manifest with
    ``n_rows == 0`` so downstream stages can distinguish "empty" from "not run".

    Returns the parquet path.
    """
    path = subset_path(pathway, base)
    path.parent.mkdir(parents=True, exist_ok=True)

    n_rows = len(gdf)
    if n_rows:
        gdf.to_parquet(path, index=False)

    has_prov = "_province" in gdf.columns and n_rows > 0
    provinces = sorted(str(p) for p in gdf["_province"].dropna().unique()) if has_prov else []
    per_province = (
        {str(k): int(v) for k, v in gdf["_province"].value_counts().items()} if has_prov else {}
    )
    manifest = {
        "pathway": pathway,
        "created_at": datetime.now(UTC).isoformat(),
        "n_rows": n_rows,
        "provinces": provinces,
        "per_province": per_province,
        "parquet_file": path.name,
        "columns": list(gdf.columns),
        "provenance": provenance or {},
    }
    manifest_path(pathway, base).write_text(
        json.dumps(manifest, indent=2, default=str), encoding="utf-8"
    )
    logger.info("MURB subset '%s': %d rows -> %s", pathway, n_rows, path)
    return path


def subset_available(pathway: str, base: Path | None = None) -> bool:
    """True if the pathway's GeoParquet exists on disk."""
    return subset_path(pathway, base).exists()


def load_subset_manifest(pathway: str, base: Path | None = None) -> dict[str, Any] | None:
    """Return the sidecar manifest dict, or None if absent."""
    mp = manifest_path(pathway, base)
    if not mp.exists():
        return None
    data: dict[str, Any] = json.loads(mp.read_text(encoding="utf-8"))
    return data


def load_murb_subset(
    pathway: str = "tiered",
    *,
    base: Path | None = None,
    columns: list[str] | None = None,
    drop_geometry: bool = False,
) -> gpd.GeoDataFrame:
    """Load a persisted MURB subset for fast downstream work.

    Parameters
    ----------
    pathway
        'precision' (confirmed + high) or 'tiered' (all positive MURBs).
    base
        Optional processed-directory override.
    columns
        Optional column projection for speed.
    drop_geometry
        If True, drop the geometry column (returns attributes only).

    Raises
    ------
    ProcessedDataUnavailableError
        If the subset has not been produced (run the full pipeline first).
    """
    path = subset_path(pathway, base)
    if not path.exists():
        msg = (
            f"MURB subset '{pathway}' not found at {path}. "
            "Run the full pipeline first: `murb-geometry run-all`."
        )
        raise ProcessedDataUnavailableError(msg)
    gdf = gpd.read_parquet(path, columns=columns)
    if drop_geometry and "geometry" in gdf.columns:
        return gdf.drop(columns=["geometry"])
    return gdf


def is_subset_valid(
    pathway: str,
    *,
    base: Path | None = None,
    expected_provenance: dict[str, Any] | None = None,
) -> tuple[bool, list[str]]:
    """Check whether a persisted subset is present and matches expected provenance.

    Returns ``(valid, reasons)``. When ``expected_provenance`` is supplied,
    mismatching keys (thresholds, type-mapping hash, CRS) mark the cache stale so
    callers can decide to reuse it only "when valid to do so".
    """
    reasons: list[str] = []
    if not subset_available(pathway, base):
        return False, [f"subset '{pathway}' not present"]
    manifest = load_subset_manifest(pathway, base)
    if manifest is None:
        reasons.append("manifest missing")
    elif expected_provenance is not None:
        stored = manifest.get("provenance", {})
        for key, val in expected_provenance.items():
            if stored.get(key) != val:
                reasons.append(f"provenance mismatch: {key}")
    return (len(reasons) == 0), reasons


def subset_status(
    base: Path | None = None,
    expected_provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Summarise availability, size, and validity of both MURB subsets."""
    status: dict[str, Any] = {}
    for pathway in PATHWAYS:
        path = subset_path(pathway, base)
        manifest = load_subset_manifest(pathway, base) or {}
        valid, reasons = is_subset_valid(
            pathway, base=base, expected_provenance=expected_provenance
        )
        status[pathway] = {
            "available": path.exists(),
            "path": str(path),
            "n_rows": manifest.get("n_rows"),
            "created_at": manifest.get("created_at"),
            "provinces": manifest.get("provinces"),
            "valid": valid,
            "invalid_reasons": reasons,
        }
    return status
