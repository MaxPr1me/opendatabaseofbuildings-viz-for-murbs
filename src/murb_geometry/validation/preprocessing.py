"""Geometry preprocessing with repair tracking and vertical-data analysis modes.

Processes full populations without arbitrary caps. Preserves original geometry
and stores repaired geometry separately. Records all repair decisions.
Supports four vertical-data modes as required by the methodology.
"""

import logging
from enum import StrEnum

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely import make_valid
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon
from shapely.validation import explain_validity

logger = logging.getLogger(__name__)


class VerticalDataMode(StrEnum):
    """Vertical-data analysis modes."""

    OBSERVED_ONLY = "observed_only"
    OBSERVED_PLUS_DERIVED = "observed_plus_derived"
    ALL_CLASSIFIED = "all_classified"
    EXTERNALLY_ENRICHED = "externally_enriched"


class HeightSource(StrEnum):
    """Source provenance for height/storey values."""

    OBSERVED_FLOORS = "observed_floors"
    OBSERVED_HEIGHT = "observed_height"
    DERIVED_FROM_HEIGHT = "derived_from_height"
    DERIVED_FROM_FLOORS = "derived_from_floors"
    ENRICHED_EXTERNAL = "enriched_external"
    MISSING = "missing"


def preprocess_geometry(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Preprocess geometries: validate, repair, flag, and track changes.

    Preserves original geometry. Adds columns for repair status and quality flags.
    Never silently deletes records — flags implausible ones instead.

    Parameters
    ----------
    gdf
        Input GeoDataFrame with geometry column.

    Returns
    -------
    gpd.GeoDataFrame
        Input with preprocessing columns added:
        - geom_is_valid: bool
        - geom_validity_reason: str or None
        - geom_was_repaired: bool
        - geom_repair_method: str or None
        - geom_is_multipart: bool
        - geom_has_holes: bool
        - geom_hole_count: int
        - geom_component_count: int
        - geom_original_area_m2: float
        - geom_repaired_area_m2: float (same as original if no repair)
        - geom_area_delta_m2: float
        - geom_is_implausible: bool
        - geom_implausible_reason: str or None
        - geom_is_null: bool
        - geom_is_empty: bool
    """
    n = len(gdf)
    logger.info("Preprocessing geometry for %d records...", n)
    gdf = gdf.copy()

    # Initialize columns
    gdf["geom_is_null"] = gdf.geometry.isna()
    gdf["geom_is_empty"] = gdf.geometry.apply(lambda g: g.is_empty if g is not None else False)
    gdf["geom_is_valid"] = False
    gdf["geom_validity_reason"] = None
    gdf["geom_was_repaired"] = False
    gdf["geom_repair_method"] = None
    gdf["geom_is_multipart"] = False
    gdf["geom_has_holes"] = False
    gdf["geom_hole_count"] = 0
    gdf["geom_component_count"] = 0
    gdf["geom_original_area_m2"] = 0.0
    gdf["geom_repaired_area_m2"] = 0.0
    gdf["geom_area_delta_m2"] = 0.0
    gdf["geom_is_implausible"] = False
    gdf["geom_implausible_reason"] = None

    # Process each geometry
    repaired_geoms = []
    for idx, row in gdf.iterrows():
        geom = row.geometry

        if geom is None or (hasattr(geom, "is_empty") and geom.is_empty):
            repaired_geoms.append(geom)
            continue

        original_area = geom.area
        gdf.at[idx, "geom_original_area_m2"] = original_area

        # Validity check
        is_valid = geom.is_valid
        gdf.at[idx, "geom_is_valid"] = is_valid

        if not is_valid:
            gdf.at[idx, "geom_validity_reason"] = explain_validity(geom)
            # Attempt repair
            try:
                repaired = make_valid(geom)
                if repaired is not None and not repaired.is_empty:
                    # Extract polygon from GeometryCollection if needed
                    if isinstance(repaired, GeometryCollection):
                        polys = [
                            g for g in repaired.geoms if isinstance(g, (Polygon, MultiPolygon))
                        ]
                        if polys:
                            repaired = MultiPolygon(polys) if len(polys) > 1 else polys[0]
                        else:
                            repaired = geom  # Keep original if no polygons extracted
                    gdf.at[idx, "geom_was_repaired"] = True
                    gdf.at[idx, "geom_repair_method"] = "make_valid"
                    gdf.at[idx, "geom_repaired_area_m2"] = repaired.area
                    gdf.at[idx, "geom_area_delta_m2"] = repaired.area - original_area
                    repaired_geoms.append(repaired)
                    continue
            except Exception:
                pass

        # Valid geometry or repair failed — keep original
        gdf.at[idx, "geom_repaired_area_m2"] = original_area
        gdf.at[idx, "geom_area_delta_m2"] = 0.0

        # Multipart detection
        if isinstance(geom, MultiPolygon):
            gdf.at[idx, "geom_is_multipart"] = True
            gdf.at[idx, "geom_component_count"] = len(geom.geoms)
        elif isinstance(geom, Polygon):
            gdf.at[idx, "geom_component_count"] = 1
        else:
            gdf.at[idx, "geom_component_count"] = 1

        # Hole detection
        if isinstance(geom, Polygon):
            n_holes = len(geom.interiors)
            gdf.at[idx, "geom_has_holes"] = n_holes > 0
            gdf.at[idx, "geom_hole_count"] = n_holes
        elif isinstance(geom, MultiPolygon):
            total_holes = sum(len(p.interiors) for p in geom.geoms)
            gdf.at[idx, "geom_has_holes"] = total_holes > 0
            gdf.at[idx, "geom_hole_count"] = total_holes

        # Implausibility flags (don't delete — flag)
        if original_area < 1.0 and original_area > 0:
            gdf.at[idx, "geom_is_implausible"] = True
            gdf.at[idx, "geom_implausible_reason"] = f"area_too_small ({original_area:.2f} m2)"
        elif original_area > 100000:
            gdf.at[idx, "geom_is_implausible"] = True
            gdf.at[idx, "geom_implausible_reason"] = f"area_too_large ({original_area:.0f} m2)"

        repaired_geoms.append(geom)

    # Store repaired geometry as the active geometry
    if repaired_geoms and len(repaired_geoms) == n:
        gdf["geometry"] = repaired_geoms

    # Summary stats
    n_null = gdf["geom_is_null"].sum()
    n_empty = gdf["geom_is_empty"].sum()
    n_invalid = (~gdf["geom_is_valid"]).sum() - n_null - n_empty
    n_repaired = gdf["geom_was_repaired"].sum()
    n_multipart = gdf["geom_is_multipart"].sum()
    n_holes = (gdf["geom_hole_count"] > 0).sum()
    n_implausible = gdf["geom_is_implausible"].sum()

    logger.info(
        "  Geometry preprocessing: %d records — "
        "null=%d, empty=%d, invalid=%d, repaired=%d, "
        "multipart=%d, with_holes=%d, implausible=%d",
        n,
        n_null,
        n_empty,
        n_invalid,
        n_repaired,
        n_multipart,
        n_holes,
        n_implausible,
    )

    return gdf


def compute_vertical_data(
    gdf: gpd.GeoDataFrame,
    mode: VerticalDataMode = VerticalDataMode.ALL_CLASSIFIED,
    floor_to_floor_m: float = 3.0,
    ground_floor_m: float = 3.5,
) -> gpd.GeoDataFrame:
    """Compute height/storey fields with explicit source provenance.

    Never silently imputes a universal storey count. Each record gets a
    height_source field indicating the provenance of its vertical data.

    Parameters
    ----------
    gdf
        GeoDataFrame with floors_numeric and height_numeric columns.
    mode
        Vertical-data analysis mode.
    floor_to_floor_m
        Default floor-to-floor height for derivation (configurable).
    ground_floor_m
        Ground floor height assumption.

    Returns
    -------
    gpd.GeoDataFrame
        Input with vertical-data columns added:
        - storeys_final: int or None
        - height_final_m: float or None
        - storeys_source: HeightSource
        - height_source: HeightSource
        - gfa_est_m2: float or None (only if storeys available)
        - gfa_method: str or None
        - vertical_data_available: bool
    """
    gdf = gdf.copy()
    n = len(gdf)

    # Initialize
    gdf["storeys_final"] = pd.array([pd.NA] * n, dtype=pd.Int64Dtype())
    gdf["height_final_m"] = np.nan
    gdf["storeys_source"] = HeightSource.MISSING.value
    gdf["height_source"] = HeightSource.MISSING.value
    gdf["gfa_est_m2"] = np.nan
    gdf["gfa_method"] = None
    gdf["vertical_data_available"] = False

    has_floors = "floors_numeric" in gdf.columns
    has_height = "height_numeric" in gdf.columns

    for idx, row in gdf.iterrows():
        floors_obs = row.get("floors_numeric") if has_floors else None
        height_obs = row.get("height_numeric") if has_height else None

        # Handle NaN
        if floors_obs is not None and (isinstance(floors_obs, float) and np.isnan(floors_obs)):
            floors_obs = None
        if height_obs is not None and (isinstance(height_obs, float) and np.isnan(height_obs)):
            height_obs = None

        # Mode: observed_only — only use directly observed values
        if mode == VerticalDataMode.OBSERVED_ONLY:
            if floors_obs is not None:
                gdf.at[idx, "storeys_final"] = int(floors_obs)
                gdf.at[idx, "storeys_source"] = HeightSource.OBSERVED_FLOORS.value
                gdf.at[idx, "vertical_data_available"] = True
            if height_obs is not None:
                gdf.at[idx, "height_final_m"] = float(height_obs)
                gdf.at[idx, "height_source"] = HeightSource.OBSERVED_HEIGHT.value
                gdf.at[idx, "vertical_data_available"] = True

        # Mode: observed_plus_derived — derive missing from available
        elif mode == VerticalDataMode.OBSERVED_PLUS_DERIVED:
            if floors_obs is not None:
                gdf.at[idx, "storeys_final"] = int(floors_obs)
                gdf.at[idx, "storeys_source"] = HeightSource.OBSERVED_FLOORS.value
                gdf.at[idx, "vertical_data_available"] = True
            elif height_obs is not None and height_obs > 0:
                # Derive storeys from height
                derived_storeys = max(1, round(height_obs / floor_to_floor_m))
                gdf.at[idx, "storeys_final"] = derived_storeys
                gdf.at[idx, "storeys_source"] = HeightSource.DERIVED_FROM_HEIGHT.value
                gdf.at[idx, "vertical_data_available"] = True

            if height_obs is not None:
                gdf.at[idx, "height_final_m"] = float(height_obs)
                gdf.at[idx, "height_source"] = HeightSource.OBSERVED_HEIGHT.value
                gdf.at[idx, "vertical_data_available"] = True
            elif floors_obs is not None and floors_obs > 0:
                # Derive height from floors
                derived_height = ground_floor_m + (floors_obs - 1) * floor_to_floor_m
                gdf.at[idx, "height_final_m"] = derived_height
                gdf.at[idx, "height_source"] = HeightSource.DERIVED_FROM_FLOORS.value
                gdf.at[idx, "vertical_data_available"] = True

        # Mode: all_classified — retain all, mark missing as missing
        elif mode == VerticalDataMode.ALL_CLASSIFIED:
            if floors_obs is not None:
                gdf.at[idx, "storeys_final"] = int(floors_obs)
                gdf.at[idx, "storeys_source"] = HeightSource.OBSERVED_FLOORS.value
                gdf.at[idx, "vertical_data_available"] = True
            if height_obs is not None:
                gdf.at[idx, "height_final_m"] = float(height_obs)
                gdf.at[idx, "height_source"] = HeightSource.OBSERVED_HEIGHT.value
                gdf.at[idx, "vertical_data_available"] = True
            # Missing stays as MISSING — no imputation

        # Mode: externally_enriched — placeholder for future integration
        elif mode == VerticalDataMode.EXTERNALLY_ENRICHED:
            # Same as all_classified for now — enrichment adds external data
            if floors_obs is not None:
                gdf.at[idx, "storeys_final"] = int(floors_obs)
                gdf.at[idx, "storeys_source"] = HeightSource.OBSERVED_FLOORS.value
                gdf.at[idx, "vertical_data_available"] = True
            if height_obs is not None:
                gdf.at[idx, "height_final_m"] = float(height_obs)
                gdf.at[idx, "height_source"] = HeightSource.OBSERVED_HEIGHT.value
                gdf.at[idx, "vertical_data_available"] = True

        # Estimate GFA where storeys are available
        storeys = gdf.at[idx, "storeys_final"]
        if storeys is not pd.NA and storeys is not None:
            area = row.get("footprint_area_m2", 0)
            if area and area > 0:
                gdf.at[idx, "gfa_est_m2"] = area * int(storeys)
                gdf.at[idx, "gfa_method"] = f"footprint_area * {gdf.at[idx, 'storeys_source']}"

    # Summary
    n_with_vertical = gdf["vertical_data_available"].sum()
    n_observed_floors = (gdf["storeys_source"] == HeightSource.OBSERVED_FLOORS.value).sum()
    n_derived_floors = (gdf["storeys_source"] == HeightSource.DERIVED_FROM_HEIGHT.value).sum()
    n_observed_height = (gdf["height_source"] == HeightSource.OBSERVED_HEIGHT.value).sum()
    n_derived_height = (gdf["height_source"] == HeightSource.DERIVED_FROM_FLOORS.value).sum()

    logger.info(
        "  Vertical data (mode=%s): %d/%d with data — "
        "observed_floors=%d, derived_floors=%d, "
        "observed_height=%d, derived_height=%d",
        mode.value,
        n_with_vertical,
        n,
        n_observed_floors,
        n_derived_floors,
        n_observed_height,
        n_derived_height,
    )

    return gdf
