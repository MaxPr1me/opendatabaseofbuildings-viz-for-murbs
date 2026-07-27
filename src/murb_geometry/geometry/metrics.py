"""Geometry metrics computation for building footprints.

All calculations assume a projected CRS (EPSG:3347) providing metric units.
Do NOT pass geometries in geographic CRS (lat/lon) — results will be invalid.

Formulas:
- Compactness (Polsby-Popper): 4π × area / perimeter²
  Range [0, 1]; circle = 1, elongated/complex < 1
- Rectangularity: area / minimum_rotated_rectangle_area
  Range [0, 1]; perfect rectangle = 1
- Convexity (Solidity): area / convex_hull_area
  Range [0, 1]; convex shape = 1
- Aspect ratio: mrr_length / mrr_width (always >= 1)
- Orientation: azimuth of major axis from north, clockwise [0, 180)
"""

import math

from shapely import Geometry
from shapely.geometry import MultiPolygon, Polygon


def footprint_area(geom: Geometry) -> float:
    """Calculate footprint area in m² (projected CRS assumed)."""
    if geom is None or geom.is_empty:
        return 0.0
    return float(geom.area)


def perimeter(geom: Geometry) -> float:
    """Calculate perimeter in metres (projected CRS assumed)."""
    if geom is None or geom.is_empty:
        return 0.0
    return float(geom.length)


def compactness(geom: Geometry) -> float:
    """Calculate Polsby-Popper compactness: 4π × area / perimeter².

    Returns
    -------
    float
        Compactness in [0, 1]. Circle = 1.
    """
    if geom is None or geom.is_empty:
        return 0.0
    a = geom.area
    p = geom.length
    if p == 0:
        return 0.0
    return (4.0 * math.pi * a) / (p * p)


def minimum_rotated_rectangle_metrics(geom: Geometry) -> dict[str, float]:
    """Calculate minimum rotated rectangle (MRR) metrics.

    Returns
    -------
    dict with keys:
        mrr_length_m: major axis length
        mrr_width_m: minor axis length
        mrr_area_m2: MRR area
        aspect_ratio: length / width (>= 1)
        orientation_deg: azimuth of major axis from north [0, 180)
    """
    if geom is None or geom.is_empty:
        return {
            "mrr_length_m": 0.0,
            "mrr_width_m": 0.0,
            "mrr_area_m2": 0.0,
            "aspect_ratio": 1.0,
            "orientation_deg": 0.0,
        }

    mrr = geom.minimum_rotated_rectangle
    if mrr is None or mrr.is_empty:
        return {
            "mrr_length_m": 0.0,
            "mrr_width_m": 0.0,
            "mrr_area_m2": 0.0,
            "aspect_ratio": 1.0,
            "orientation_deg": 0.0,
        }

    coords = list(mrr.exterior.coords)
    # MRR has 5 coords (closed ring), 4 unique corners
    # Calculate edge lengths
    edges = []
    for i in range(4):
        dx = coords[i + 1][0] - coords[i][0]
        dy = coords[i + 1][1] - coords[i][1]
        length = math.sqrt(dx * dx + dy * dy)
        angle = math.degrees(math.atan2(dx, dy)) % 180  # azimuth from north
        edges.append((length, angle, dx, dy))

    # Major axis is the longer edge pair
    edge_a = edges[0][0]
    edge_b = edges[1][0]

    if edge_a >= edge_b:
        mrr_length = edge_a
        mrr_width = edge_b
        orientation = edges[0][1]
    else:
        mrr_length = edge_b
        mrr_width = edge_a
        orientation = edges[1][1]

    aspect_ratio = mrr_length / mrr_width if mrr_width > 0 else 1.0

    return {
        "mrr_length_m": mrr_length,
        "mrr_width_m": mrr_width,
        "mrr_area_m2": float(mrr.area),
        "aspect_ratio": aspect_ratio,
        "orientation_deg": orientation,
    }


def rectangularity(geom: Geometry) -> float:
    """Calculate rectangularity: area / MRR area.

    Returns
    -------
    float
        Rectangularity in [0, 1]. Perfect rectangle = 1.
    """
    if geom is None or geom.is_empty:
        return 0.0
    mrr = geom.minimum_rotated_rectangle
    if mrr is None or mrr.is_empty or mrr.area == 0:
        return 0.0
    return float(geom.area / mrr.area)


def convexity(geom: Geometry) -> float:
    """Calculate convexity (solidity): area / convex_hull_area.

    Returns
    -------
    float
        Convexity in [0, 1]. Convex polygon = 1.
    """
    if geom is None or geom.is_empty:
        return 0.0
    hull = geom.convex_hull
    if hull is None or hull.is_empty or hull.area == 0:
        return 0.0
    return float(geom.area / hull.area)


def hole_metrics(geom: Geometry) -> dict[str, float | int]:
    """Calculate hole (interior ring) metrics.

    Returns
    -------
    dict with keys:
        hole_count: number of interior rings
        hole_area_m2: total area of holes
        hole_fraction: hole_area / total_exterior_area
    """
    if geom is None or geom.is_empty:
        return {"hole_count": 0, "hole_area_m2": 0.0, "hole_fraction": 0.0}

    hole_count = 0
    hole_area = 0.0

    if isinstance(geom, Polygon):
        hole_count = len(list(geom.interiors))
        for interior in geom.interiors:
            hole_area += Polygon(interior).area
    elif isinstance(geom, MultiPolygon):
        for poly in geom.geoms:
            hole_count += len(list(poly.interiors))
            for interior in poly.interiors:
                hole_area += Polygon(interior).area

    exterior_area = geom.area + hole_area  # gross area including holes
    hole_fraction = hole_area / exterior_area if exterior_area > 0 else 0.0

    return {
        "hole_count": hole_count,
        "hole_area_m2": hole_area,
        "hole_fraction": hole_fraction,
    }


def component_count(geom: Geometry) -> int:
    """Count disconnected polygon components."""
    if geom is None or geom.is_empty:
        return 0
    if isinstance(geom, MultiPolygon):
        return len(geom.geoms)
    return 1


def vertex_count(geom: Geometry) -> int:
    """Count total vertices in the geometry."""
    if geom is None or geom.is_empty:
        return 0
    geom.exterior.coords if isinstance(geom, Polygon) else []
    if isinstance(geom, Polygon):
        total = len(geom.exterior.coords)
        for interior in geom.interiors:
            total += len(interior.coords)
        return total
    elif isinstance(geom, MultiPolygon):
        total = 0
        for poly in geom.geoms:
            total += len(poly.exterior.coords)
            for interior in poly.interiors:
                total += len(interior.coords)
        return total
    return 0


def compute_geometry_metrics(geom: Geometry) -> dict[str, float | int]:
    """Compute all geometry metrics for a single building footprint.

    Parameters
    ----------
    geom
        A shapely Polygon or MultiPolygon in a projected CRS (metres).

    Returns
    -------
    dict
        Dictionary of all computed metrics.
    """
    mrr = minimum_rotated_rectangle_metrics(geom)
    holes = hole_metrics(geom)

    return {
        "footprint_area_m2": footprint_area(geom),
        "perimeter_m": perimeter(geom),
        "compactness": compactness(geom),
        "rectangularity": rectangularity(geom),
        "convexity": convexity(geom),
        "mrr_length_m": mrr["mrr_length_m"],
        "mrr_width_m": mrr["mrr_width_m"],
        "mrr_area_m2": mrr["mrr_area_m2"],
        "aspect_ratio": mrr["aspect_ratio"],
        "orientation_deg": mrr["orientation_deg"],
        "hole_count": holes["hole_count"],
        "hole_area_m2": holes["hole_area_m2"],
        "hole_fraction": holes["hole_fraction"],
        "component_count": component_count(geom),
        "vertex_count": vertex_count(geom),
    }
