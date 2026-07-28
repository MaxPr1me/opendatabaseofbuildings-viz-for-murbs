"""Full-population MURB pipeline — Option C multi-pathway processing.

Processes all 15 GeoPackage files without arbitrary row caps.
Implements two classification pathways in parallel:
  1. Precision — direct authoritative evidence only (type or units)
  2. Tiered — precision plus probable/possible from floors, height, area

Produces persisted GeoParquet per pathway for downstream stages.
"""

import hashlib
import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import geopandas as gpd
import numpy as np
import pandas as pd

from murb_geometry.classification.classifier import (
    ClassificationResult,
    classify_building,
    normalize_type_value,
)
from murb_geometry.config import load_config
from murb_geometry.geometry.metrics import compute_geometry_metrics
from murb_geometry.statistics.descriptive import compute_descriptive_stats

logger = logging.getLogger(__name__)

# Province file mapping — merges split files for ON and QC
PROVINCE_FILES: dict[str, list[str]] = {
    "AB": ["data/ODB_v3_AB/ODB_v3_AB.gpkg"],
    "BC": ["data/ODB_v3_BC/ODB_v3_BC.gpkg"],
    "MB": ["data/ODB_v3_MB/ODB_v3_MB.gpkg"],
    "NB": ["data/ODB_v3_NB/ODB_v3_NB.gpkg"],
    "NL": ["data/ODB_v3_NL/ODB_v3_NL.gpkg"],
    "NS": ["data/ODB_v3_NS/ODB_v3_NS.gpkg"],
    "NT": ["data/ODB_v3_NT/ODB_v3_NT.gpkg"],
    "ON": [
        "data/ODB_v3_ON_1/ODB_v3_ON_1.gpkg",
        "data/ODB_v3_ON_2/ODB_v3_ON_2.gpkg",
        "data/ODB_v3_ON_3/ODB_v3_ON_3.gpkg",
    ],
    "PE": ["data/ODB_v3_PE/ODB_v3_PE.gpkg"],
    "QC": [
        "data/ODB_v3_QC_1/ODB_v3_QC_1.gpkg",
        "data/ODB_v3_QC_2/ODB_v3_QC_2.gpkg",
    ],
    "SK": ["data/ODB_v3_SK/ODB_v3_SK.gpkg"],
    "YT": ["data/ODB_v3_YT/ODB_v3_YT.gpkg"],
}

# Confidence levels that qualify for each pathway
PRECISION_LEVELS = {"confirmed_murb", "high_confidence_murb"}
TIERED_LEVELS = {"confirmed_murb", "high_confidence_murb", "probable_murb", "possible_murb"}


def _parse_numeric(value: Any, missing_markers: list[str] | None = None) -> float | None:
    """Parse a TEXT field to numeric, returning None for missing/invalid."""
    if missing_markers is None:
        missing_markers = ["..", "", "NA", "N/A"]
    if value is None:
        return None
    # Handle pandas NaN
    if isinstance(value, float) and np.isnan(value):
        return None
    s = str(value).strip()
    if s in missing_markers:
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _parse_int(value: Any, missing_markers: list[str] | None = None) -> int | None:
    """Parse a TEXT field to integer, returning None for missing/invalid."""
    f = _parse_numeric(value, missing_markers)
    if f is None:
        return None
    return int(f)


def _file_hash(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_province_data(
    province: str,
    file_paths: list[str],
    data_dir: Path | None = None,
) -> gpd.GeoDataFrame:
    """Load all GeoPackage files for a province without row limits.

    Merges split files (ON, QC) into a single GeoDataFrame.
    No WHERE clause filtering — classification happens after loading.

    Parameters
    ----------
    province
        Province code (e.g., "ON", "NS").
    file_paths
        List of relative GeoPackage paths.
    data_dir
        Optional override for base directory resolution.

    Returns
    -------
    gpd.GeoDataFrame
        Complete province data with all rows and columns.
    """
    base = data_dir or Path(".")
    gdfs: list[gpd.GeoDataFrame] = []

    for fpath in file_paths:
        full_path = base / fpath
        if not full_path.exists():
            logger.warning("File not found: %s — skipping", full_path)
            continue

        logger.info("Loading %s (full population)...", full_path.name)
        t0 = time.time()
        gdf = gpd.read_file(full_path)
        elapsed = time.time() - t0
        logger.info("  Loaded %d records in %.1fs", len(gdf), elapsed)
        gdf["_source_file"] = full_path.name
        gdf["_province"] = province
        gdfs.append(gdf)

    if not gdfs:
        logger.warning("No data loaded for %s", province)
        return gpd.GeoDataFrame()

    if len(gdfs) == 1:
        return gdfs[0]

    merged = pd.concat(gdfs, ignore_index=True)
    result = gpd.GeoDataFrame(merged, geometry="geometry")
    logger.info("  Merged %d files → %d records for %s", len(gdfs), len(result), province)
    return result


def classify_dataframe(
    gdf: gpd.GeoDataFrame,
    min_murb_units: int = 4,
    min_candidate_area_m2: float = 200.0,
    missing_markers: list[str] | None = None,
) -> gpd.GeoDataFrame:
    """Apply MURB classification to every row in a GeoDataFrame.

    Adds columns: type_normalized, units_numeric, floors_numeric, height_numeric,
    confidence_level, confidence_score, rule_id, rule_name, evidence_fields, reasoning.

    No rows are excluded — all records receive a classification.

    Parameters
    ----------
    gdf
        Input GeoDataFrame with ODB columns (type, units, floors, height).
    min_murb_units
        Minimum dwelling units threshold.
    min_candidate_area_m2
        Minimum footprint area for geometric candidates.
    missing_markers
        Values to treat as missing.

    Returns
    -------
    gpd.GeoDataFrame
        Input with classification columns added.
    """
    if missing_markers is None:
        missing_markers = ["..", "", "NA", "N/A"]

    n = len(gdf)
    logger.info("Classifying %d buildings...", n)

    # Parse fields vectorized where possible
    gdf = gdf.copy()

    def _safe_normalize_type(v: Any) -> str | None:
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return None
        return normalize_type_value(v)

    gdf["type_normalized"] = (
        gdf["type"].apply(_safe_normalize_type) if "type" in gdf.columns else None
    )
    gdf["units_numeric"] = (
        gdf["units"].apply(lambda v: _parse_int(v, missing_markers))
        if "units" in gdf.columns
        else None
    )
    gdf["floors_numeric"] = (
        gdf["floors"].apply(lambda v: _parse_int(v, missing_markers))
        if "floors" in gdf.columns
        else None
    )
    gdf["height_numeric"] = (
        gdf["height"].apply(lambda v: _parse_numeric(v, missing_markers))
        if "height" in gdf.columns
        else None
    )

    # Compute footprint area for classification (geometry must be in projected CRS)
    gdf["footprint_area_m2"] = gdf.geometry.area

    # Classify each building
    results: list[ClassificationResult] = []
    for _, row in gdf.iterrows():
        result = classify_building(
            type_normalized=row.get("type_normalized"),
            units_numeric=row.get("units_numeric"),
            floors_numeric=row.get("floors_numeric"),
            footprint_area_m2=row.get("footprint_area_m2"),
            height_numeric=row.get("height_numeric"),
            min_murb_units=min_murb_units,
            min_candidate_area_m2=min_candidate_area_m2,
        )
        results.append(result)

    gdf["confidence_level"] = [r.confidence_level for r in results]
    gdf["confidence_score"] = [r.confidence_score for r in results]
    gdf["rule_id"] = [r.rule_id for r in results]
    gdf["rule_name"] = [r.rule_name for r in results]
    gdf["evidence_fields"] = [",".join(r.evidence_fields) for r in results]
    gdf["reasoning"] = [r.reasoning for r in results]

    # Log classification summary
    counts = gdf["confidence_level"].value_counts()
    for level, count in counts.items():
        logger.info("  %s: %d (%.1f%%)", level, count, 100 * count / n)

    return gdf


def compute_metrics_vectorized(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Compute geometry metrics for classified buildings.

    Uses vectorized shapely operations where possible, falls back to
    row-by-row for complex metrics.

    Parameters
    ----------
    gdf
        GeoDataFrame with valid geometries (projected CRS).

    Returns
    -------
    gpd.GeoDataFrame
        Input with geometry metric columns added.
    """
    n = len(gdf)
    logger.info("Computing geometry metrics for %d buildings...", n)
    gdf = gdf.copy()

    # Vectorized basic metrics
    gdf["perimeter_m"] = gdf.geometry.length
    gdf["compactness"] = (4.0 * np.pi * gdf["footprint_area_m2"]) / (gdf["perimeter_m"] ** 2)

    # Row-by-row for complex metrics (MRR, convexity, holes)
    mrr_lengths = []
    mrr_widths = []
    mrr_areas = []
    aspect_ratios = []
    orientations = []
    convexities = []
    rectangularities = []
    hole_counts = []
    hole_areas = []
    vertex_counts = []

    t0 = time.time()
    for i, (_, row) in enumerate(gdf.iterrows()):
        if i > 0 and i % 10000 == 0:
            elapsed = time.time() - t0
            rate = i / elapsed
            logger.info("  Metrics: %d/%d (%.0f/sec)", i, n, rate)

        geom = row.geometry
        metrics = compute_geometry_metrics(geom)
        mrr_lengths.append(metrics["mrr_length_m"])
        mrr_widths.append(metrics["mrr_width_m"])
        mrr_areas.append(metrics["mrr_area_m2"])
        aspect_ratios.append(metrics["aspect_ratio"])
        orientations.append(metrics["orientation_deg"])
        convexities.append(metrics["convexity"])
        rectangularities.append(metrics["rectangularity"])
        hole_counts.append(metrics["hole_count"])
        hole_areas.append(metrics["hole_area_m2"])
        vertex_counts.append(metrics["vertex_count"])

    gdf["mrr_length_m"] = mrr_lengths
    gdf["mrr_width_m"] = mrr_widths
    gdf["mrr_area_m2"] = mrr_areas
    gdf["aspect_ratio"] = aspect_ratios
    gdf["orientation_deg"] = orientations
    gdf["convexity"] = convexities
    gdf["rectangularity"] = rectangularities
    gdf["hole_count"] = hole_counts
    gdf["hole_area_m2"] = hole_areas
    gdf["vertex_count"] = vertex_counts

    elapsed = time.time() - t0
    logger.info("  Metrics complete: %d buildings in %.1fs", n, elapsed)
    return gdf


def filter_pathway(
    gdf: gpd.GeoDataFrame,
    pathway: str,
) -> gpd.GeoDataFrame:
    """Filter classified buildings by pathway.

    Parameters
    ----------
    gdf
        Classified GeoDataFrame with confidence_level column.
    pathway
        Either "precision" or "tiered".

    Returns
    -------
    gpd.GeoDataFrame
        Subset matching the pathway confidence levels.
    """
    if pathway == "precision":
        levels = PRECISION_LEVELS
    elif pathway == "tiered":
        levels = TIERED_LEVELS
    else:
        msg = f"Unknown pathway: {pathway}. Use 'precision' or 'tiered'."
        raise ValueError(msg)

    filtered = gdf[gdf["confidence_level"].isin(levels)].copy()
    logger.info(
        "Pathway '%s': %d/%d buildings (%.1f%%)",
        pathway,
        len(filtered),
        len(gdf),
        100 * len(filtered) / max(len(gdf), 1),
    )
    return filtered


def process_province(
    province: str,
    file_paths: list[str],
    config: Any,
    data_dir: Path | None = None,
) -> dict[str, Any]:
    """Process a single province through classification and metrics.

    Returns
    -------
    dict with keys: province, total_records, classified, precision_count, tiered_count,
    precision_gdf, tiered_gdf, stats, timing
    """
    t0 = time.time()

    # Load full population
    gdf = load_province_data(province, file_paths, data_dir)
    if gdf.empty:
        return {"province": province, "total_records": 0, "error": "no data loaded"}

    total = len(gdf)

    # Classify all buildings
    gdf = classify_dataframe(
        gdf,
        min_murb_units=config.classification.minimum_murb_units,
        min_candidate_area_m2=config.classification.footprint_area["minimum_candidate_m2"],
        missing_markers=config.input.missing_value_markers,
    )

    # Filter by pathway
    precision_gdf = filter_pathway(gdf, "precision")
    tiered_gdf = filter_pathway(gdf, "tiered")

    # Compute metrics only for classified MURBs
    precision_with_metrics = gpd.GeoDataFrame()
    tiered_with_metrics = gpd.GeoDataFrame()

    if not precision_gdf.empty:
        precision_with_metrics = compute_metrics_vectorized(precision_gdf)
    if not tiered_gdf.empty:
        tiered_with_metrics = compute_metrics_vectorized(tiered_gdf)

    elapsed = time.time() - t0
    logger.info(
        "%s complete: %d total, %d precision, %d tiered (%.1fs)",
        province,
        total,
        len(precision_gdf),
        len(tiered_gdf),
        elapsed,
    )

    return {
        "province": province,
        "total_records": total,
        "precision_count": len(precision_gdf),
        "tiered_count": len(tiered_gdf),
        "precision_gdf": precision_with_metrics,
        "tiered_gdf": tiered_with_metrics,
        "classification_summary": gdf["confidence_level"].value_counts().to_dict(),
        "timing_seconds": elapsed,
    }


def run_full_pipeline(
    config_path: str = "config/default.yaml",
    provinces: list[str] | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Execute the complete multi-pathway pipeline on all provinces.

    Parameters
    ----------
    config_path
        Path to YAML configuration.
    provinces
        Optional subset of provinces to process. None = all.
    output_dir
        Output directory override.

    Returns
    -------
    dict
        Complete run manifest with timings, counts, and output paths.
    """
    config = load_config(config_path=config_path, local_path="config/local.yaml")
    out = output_dir or Path(config.paths.output_dir)
    data_dir = Path(".")

    # Create output directories
    for subdir in ["reports", "archetypes", "gbxml", "excel", "figures"]:
        (out / subdir).mkdir(parents=True, exist_ok=True)
    Path("data/processed").mkdir(parents=True, exist_ok=True)

    target_provinces = provinces or list(PROVINCE_FILES.keys())
    logger.info("Starting full pipeline — %d provinces", len(target_provinces))

    manifest: dict[str, Any] = {
        "started_at": datetime.now(UTC).isoformat(),
        "config_path": config_path,
        "classification_pathway": "Option C — Multi-pathway",
        "precision_levels": sorted(PRECISION_LEVELS),
        "tiered_levels": sorted(TIERED_LEVELS),
        "provinces_requested": target_provinces,
        "stages": {},
    }

    # Stage 1: Process all provinces
    all_precision: list[gpd.GeoDataFrame] = []
    all_tiered: list[gpd.GeoDataFrame] = []
    province_results: dict[str, dict] = {}

    for prov in target_provinces:
        if prov not in PROVINCE_FILES:
            logger.warning("Unknown province code: %s — skipping", prov)
            continue

        result = process_province(
            province=prov,
            file_paths=PROVINCE_FILES[prov],
            config=config,
            data_dir=data_dir,
        )
        province_results[prov] = result

        if not result.get("precision_gdf", gpd.GeoDataFrame()).empty:
            all_precision.append(result["precision_gdf"])
        if not result.get("tiered_gdf", gpd.GeoDataFrame()).empty:
            all_tiered.append(result["tiered_gdf"])

    # Stage 2: Combine national datasets
    national_precision = gpd.GeoDataFrame()
    national_tiered = gpd.GeoDataFrame()

    if all_precision:
        national_precision = pd.concat(all_precision, ignore_index=True)
        national_precision = gpd.GeoDataFrame(national_precision, geometry="geometry")
        logger.info("National precision population: %d buildings", len(national_precision))

    if all_tiered:
        national_tiered = pd.concat(all_tiered, ignore_index=True)
        national_tiered = gpd.GeoDataFrame(national_tiered, geometry="geometry")
        logger.info("National tiered population: %d buildings", len(national_tiered))

    # Stage 3: Persist processed data as GeoParquet
    if not national_precision.empty:
        precision_path = Path("data/processed/murbs_precision.parquet")
        national_precision.to_parquet(precision_path, index=False)
        logger.info("Saved precision pathway: %s", precision_path)

    if not national_tiered.empty:
        tiered_path = Path("data/processed/murbs_tiered.parquet")
        national_tiered.to_parquet(tiered_path, index=False)
        logger.info("Saved tiered pathway: %s", tiered_path)

    # Stage 4: Compute summary statistics per pathway
    stats = _compute_pathway_statistics(national_precision, national_tiered, province_results)

    # Stage 5: Generate classification summary report
    classification_summary = _generate_classification_report(province_results, out)

    # Stage 6: Generate pathway sensitivity report
    sensitivity = _generate_sensitivity_report(national_precision, national_tiered, out)

    # Finalize manifest
    manifest["completed_at"] = datetime.now(UTC).isoformat()
    manifest["stages"]["province_processing"] = {
        prov: {
            "total_records": r.get("total_records", 0),
            "precision_count": r.get("precision_count", 0),
            "tiered_count": r.get("tiered_count", 0),
            "timing_seconds": r.get("timing_seconds", 0),
            "classification_summary": r.get("classification_summary", {}),
        }
        for prov, r in province_results.items()
    }
    manifest["stages"]["national_totals"] = {
        "precision_buildings": len(national_precision),
        "tiered_buildings": len(national_tiered),
    }
    manifest["stages"]["statistics"] = stats
    manifest["stages"]["classification_report"] = str(classification_summary)
    manifest["stages"]["sensitivity_report"] = str(sensitivity)

    # Save manifest
    manifest_path = out / "reports" / "run_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, default=str)
    logger.info("Run manifest: %s", manifest_path)

    return manifest


def _compute_pathway_statistics(
    precision: gpd.GeoDataFrame,
    tiered: gpd.GeoDataFrame,
    province_results: dict[str, dict],
) -> dict[str, Any]:
    """Compute descriptive statistics for each pathway."""
    stats: dict[str, Any] = {}

    for pathway_name, gdf in [("precision", precision), ("tiered", tiered)]:
        if gdf.empty:
            stats[pathway_name] = {"n": 0}
            continue

        metric_fields = [
            "footprint_area_m2",
            "aspect_ratio",
            "compactness",
            "rectangularity",
            "convexity",
            "mrr_length_m",
            "mrr_width_m",
            "perimeter_m",
            "orientation_deg",
        ]
        pathway_stats: dict[str, Any] = {"n": len(gdf)}
        for field in metric_fields:
            if field in gdf.columns:
                values = gdf[field].dropna().tolist()
                if values:
                    pathway_stats[field] = compute_descriptive_stats(values, field)

        # Floors/units if available
        for field in ["floors_numeric", "units_numeric"]:
            if field in gdf.columns:
                values = gdf[field].dropna().tolist()
                if values:
                    pathway_stats[field] = compute_descriptive_stats(values, field)

        stats[pathway_name] = pathway_stats

    return stats


def _generate_classification_report(
    province_results: dict[str, dict],
    output_dir: Path,
) -> Path:
    """Generate classification summary CSV."""
    rows: list[dict] = []
    for prov, result in province_results.items():
        summary = result.get("classification_summary", {})
        for level, count in summary.items():
            rows.append(
                {
                    "province": prov,
                    "confidence_level": level,
                    "count": count,
                    "total_records": result.get("total_records", 0),
                    "percentage": round(100 * count / max(result.get("total_records", 1), 1), 2),
                }
            )

    if rows:
        df = pd.DataFrame(rows)
        path = output_dir / "reports" / "classification_summary.csv"
        df.to_csv(path, index=False)
        logger.info("Classification report: %s", path)
        return path
    return output_dir / "reports" / "classification_summary.csv"


def _generate_sensitivity_report(
    precision: gpd.GeoDataFrame,
    tiered: gpd.GeoDataFrame,
    output_dir: Path,
) -> Path:
    """Generate pathway sensitivity comparison."""
    rows: list[dict] = []

    for metric in ["footprint_area_m2", "aspect_ratio", "compactness", "rectangularity"]:
        for pathway_name, gdf in [("precision", precision), ("tiered", tiered)]:
            if gdf.empty or metric not in gdf.columns:
                continue
            values = gdf[metric].dropna().tolist()
            if not values:
                continue
            stats = compute_descriptive_stats(values, metric)
            rows.append(
                {
                    "metric": metric,
                    "pathway": pathway_name,
                    "n": stats["valid_count"],
                    "median": stats["median"],
                    "mean": stats["mean"],
                    "p25": stats["p25"],
                    "p75": stats["p75"],
                    "p5": stats["p5"],
                    "p95": stats["p95"],
                }
            )

    if rows:
        df = pd.DataFrame(rows)
        path = output_dir / "reports" / "pathway_sensitivity.csv"
        df.to_csv(path, index=False)
        logger.info("Sensitivity report: %s", path)
        return path
    return output_dir / "reports" / "pathway_sensitivity.csv"
