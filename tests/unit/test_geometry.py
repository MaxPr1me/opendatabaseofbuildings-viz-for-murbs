"""Unit tests for geometry metrics using known synthetic polygons.

All test polygons are defined in a projected CRS coordinate space (metres).
Expected values are calculated analytically.
"""

import math

import pytest
from shapely.geometry import MultiPolygon, Polygon

from murb_geometry.geometry.metrics import (
    compactness,
    component_count,
    compute_geometry_metrics,
    convexity,
    footprint_area,
    hole_metrics,
    minimum_rotated_rectangle_metrics,
    perimeter,
    rectangularity,
    vertex_count,
)

# --- Test fixtures: synthetic polygons ---


@pytest.fixture
def square_10x10() -> Polygon:
    """10m × 10m square aligned with axes."""
    return Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])


@pytest.fixture
def rectangle_20x5() -> Polygon:
    """20m × 5m rectangle aligned with axes (long axis E-W)."""
    return Polygon([(0, 0), (20, 0), (20, 5), (0, 5)])


@pytest.fixture
def rotated_rectangle() -> Polygon:
    """10m × 5m rectangle rotated 45 degrees."""
    # Centre at origin, rotate 45°
    import math

    cos45 = math.cos(math.radians(45))
    sin45 = math.sin(math.radians(45))
    # Half-lengths: 5 along major, 2.5 along minor
    corners = [(-5, -2.5), (5, -2.5), (5, 2.5), (-5, 2.5)]
    rotated = [(x * cos45 - y * sin45, x * sin45 + y * cos45) for x, y in corners]
    return Polygon(rotated)


@pytest.fixture
def l_shape() -> Polygon:
    """L-shaped polygon."""
    return Polygon([(0, 0), (10, 0), (10, 5), (5, 5), (5, 10), (0, 10)])


@pytest.fixture
def polygon_with_hole() -> Polygon:
    """20m × 20m square with a 10m × 10m central hole (courtyard)."""
    exterior = [(0, 0), (20, 0), (20, 20), (0, 20)]
    interior = [(5, 5), (15, 5), (15, 15), (5, 15)]
    return Polygon(exterior, [interior])


@pytest.fixture
def multipart_geometry() -> MultiPolygon:
    """Two disconnected 5m × 5m squares."""
    poly1 = Polygon([(0, 0), (5, 0), (5, 5), (0, 5)])
    poly2 = Polygon([(20, 20), (25, 20), (25, 25), (20, 25)])
    return MultiPolygon([poly1, poly2])


@pytest.fixture
def empty_polygon() -> Polygon:
    """Empty polygon."""
    return Polygon()


# --- Tests: footprint_area ---


def test_area_square(square_10x10: Polygon) -> None:
    """Square area is 100 m²."""
    assert footprint_area(square_10x10) == pytest.approx(100.0)


def test_area_rectangle(rectangle_20x5: Polygon) -> None:
    """Rectangle area is 100 m²."""
    assert footprint_area(rectangle_20x5) == pytest.approx(100.0)


def test_area_polygon_with_hole(polygon_with_hole: Polygon) -> None:
    """Area excludes the hole: 400 - 100 = 300 m²."""
    assert footprint_area(polygon_with_hole) == pytest.approx(300.0)


def test_area_empty(empty_polygon: Polygon) -> None:
    """Empty polygon has zero area."""
    assert footprint_area(empty_polygon) == 0.0


def test_area_none() -> None:
    """None geometry returns zero."""
    assert footprint_area(None) == 0.0


# --- Tests: perimeter ---


def test_perimeter_square(square_10x10: Polygon) -> None:
    """Square perimeter is 40 m."""
    assert perimeter(square_10x10) == pytest.approx(40.0)


def test_perimeter_rectangle(rectangle_20x5: Polygon) -> None:
    """Rectangle perimeter is 50 m."""
    assert perimeter(rectangle_20x5) == pytest.approx(50.0)


# --- Tests: compactness ---


def test_compactness_square(square_10x10: Polygon) -> None:
    """Square compactness = 4π × 100 / 1600 = π/4 ≈ 0.785."""
    expected = math.pi / 4.0
    assert compactness(square_10x10) == pytest.approx(expected, rel=1e-3)


def test_compactness_rectangle(rectangle_20x5: Polygon) -> None:
    """Elongated rectangle has lower compactness than square."""
    c = compactness(rectangle_20x5)
    assert c < compactness(Polygon([(0, 0), (10, 0), (10, 10), (0, 10)]))
    assert c > 0


# --- Tests: minimum rotated rectangle ---


def test_mrr_square(square_10x10: Polygon) -> None:
    """Square MRR has aspect ratio ~1."""
    mrr = minimum_rotated_rectangle_metrics(square_10x10)
    assert mrr["mrr_length_m"] == pytest.approx(10.0, rel=1e-3)
    assert mrr["mrr_width_m"] == pytest.approx(10.0, rel=1e-3)
    assert mrr["aspect_ratio"] == pytest.approx(1.0, rel=1e-2)


def test_mrr_rectangle(rectangle_20x5: Polygon) -> None:
    """20×5 rectangle has aspect ratio 4."""
    mrr = minimum_rotated_rectangle_metrics(rectangle_20x5)
    assert mrr["mrr_length_m"] == pytest.approx(20.0, rel=1e-3)
    assert mrr["mrr_width_m"] == pytest.approx(5.0, rel=1e-3)
    assert mrr["aspect_ratio"] == pytest.approx(4.0, rel=1e-2)


def test_mrr_orientation_ew_rectangle(rectangle_20x5: Polygon) -> None:
    """E-W rectangle has orientation ~90° (east from north)."""
    mrr = minimum_rotated_rectangle_metrics(rectangle_20x5)
    # Major axis is along x-axis (east), so azimuth from north = 90°
    assert mrr["orientation_deg"] == pytest.approx(90.0, abs=1.0)


# --- Tests: rectangularity ---


def test_rectangularity_square(square_10x10: Polygon) -> None:
    """Square has rectangularity ~1.0."""
    assert rectangularity(square_10x10) == pytest.approx(1.0, rel=1e-3)


def test_rectangularity_l_shape(l_shape: Polygon) -> None:
    """L-shape has rectangularity < 1.0."""
    r = rectangularity(l_shape)
    assert 0.5 < r < 1.0


# --- Tests: convexity ---


def test_convexity_square(square_10x10: Polygon) -> None:
    """Convex square has convexity = 1.0."""
    assert convexity(square_10x10) == pytest.approx(1.0, rel=1e-6)


def test_convexity_l_shape(l_shape: Polygon) -> None:
    """L-shape is non-convex."""
    c = convexity(l_shape)
    assert 0.5 < c < 1.0


# --- Tests: hole_metrics ---


def test_holes_polygon_with_hole(polygon_with_hole: Polygon) -> None:
    """Courtyard polygon has 1 hole of 100 m²."""
    h = hole_metrics(polygon_with_hole)
    assert h["hole_count"] == 1
    assert h["hole_area_m2"] == pytest.approx(100.0)
    assert h["hole_fraction"] == pytest.approx(100.0 / 400.0)  # 25%


def test_holes_no_hole(square_10x10: Polygon) -> None:
    """Square has no holes."""
    h = hole_metrics(square_10x10)
    assert h["hole_count"] == 0
    assert h["hole_area_m2"] == 0.0


# --- Tests: component_count ---


def test_component_count_single(square_10x10: Polygon) -> None:
    """Single polygon has 1 component."""
    assert component_count(square_10x10) == 1


def test_component_count_multi(multipart_geometry: MultiPolygon) -> None:
    """MultiPolygon has 2 components."""
    assert component_count(multipart_geometry) == 2


# --- Tests: vertex_count ---


def test_vertex_count_square(square_10x10: Polygon) -> None:
    """Square has 5 vertices (closed ring)."""
    assert vertex_count(square_10x10) == 5


def test_vertex_count_with_hole(polygon_with_hole: Polygon) -> None:
    """Polygon with hole has exterior + interior vertices."""
    v = vertex_count(polygon_with_hole)
    assert v == 10  # 5 exterior + 5 interior (closed rings)


# --- Tests: compute_geometry_metrics ---


def test_compute_geometry_metrics_complete(square_10x10: Polygon) -> None:
    """compute_geometry_metrics returns all expected keys."""
    metrics = compute_geometry_metrics(square_10x10)
    expected_keys = {
        "footprint_area_m2",
        "perimeter_m",
        "compactness",
        "rectangularity",
        "convexity",
        "mrr_length_m",
        "mrr_width_m",
        "mrr_area_m2",
        "aspect_ratio",
        "orientation_deg",
        "hole_count",
        "hole_area_m2",
        "hole_fraction",
        "component_count",
        "vertex_count",
    }
    assert set(metrics.keys()) == expected_keys


def test_compute_geometry_metrics_values(rectangle_20x5: Polygon) -> None:
    """compute_geometry_metrics returns correct values for a known rectangle."""
    metrics = compute_geometry_metrics(rectangle_20x5)
    assert metrics["footprint_area_m2"] == pytest.approx(100.0)
    assert metrics["perimeter_m"] == pytest.approx(50.0)
    assert metrics["aspect_ratio"] == pytest.approx(4.0, rel=1e-2)
    assert metrics["rectangularity"] == pytest.approx(1.0, rel=1e-3)
    assert metrics["convexity"] == pytest.approx(1.0, rel=1e-6)
    assert metrics["hole_count"] == 0
    assert metrics["component_count"] == 1
