"""Unit tests for synthetic parametric geometry generators."""

import math

import pytest

from murb_geometry.archetypes.synthetic import (
    generate_courtyard,
    generate_l_shape,
    generate_rectangle,
    generate_t_shape,
    generate_u_shape,
)


def test_rectangle_area() -> None:
    """Rectangle has correct target area."""
    poly = generate_rectangle(area_m2=400.0, aspect_ratio=2.0)
    assert poly.area == pytest.approx(400.0, rel=1e-6)


def test_rectangle_aspect_ratio() -> None:
    """Rectangle has correct aspect ratio."""
    poly = generate_rectangle(area_m2=400.0, aspect_ratio=4.0)
    mrr = poly.minimum_rotated_rectangle
    coords = list(mrr.exterior.coords)
    edges = []
    for i in range(4):
        dx = coords[i + 1][0] - coords[i][0]
        dy = coords[i + 1][1] - coords[i][1]
        edges.append(math.sqrt(dx * dx + dy * dy))
    long_edge = max(edges)
    short_edge = min(edges)
    assert long_edge / short_edge == pytest.approx(4.0, rel=1e-2)


def test_rectangle_orientation() -> None:
    """Rotated rectangle is valid and has correct area."""
    poly = generate_rectangle(area_m2=200.0, aspect_ratio=2.0, orientation_deg=45.0)
    assert poly.is_valid
    assert poly.area == pytest.approx(200.0, rel=1e-6)


def test_l_shape_area() -> None:
    """L-shape approximates target area."""
    poly = generate_l_shape(area_m2=500.0, aspect_ratio=2.0)
    assert poly.is_valid
    assert poly.area == pytest.approx(500.0, rel=0.05)


def test_l_shape_has_6_vertices() -> None:
    """L-shape has 6 unique vertices (7 in closed ring)."""
    poly = generate_l_shape(area_m2=500.0)
    assert len(poly.exterior.coords) == 7  # closed ring


def test_u_shape_area() -> None:
    """U-shape approximates target area."""
    poly = generate_u_shape(area_m2=600.0)
    assert poly.is_valid
    assert poly.area == pytest.approx(600.0, rel=0.05)


def test_courtyard_area() -> None:
    """Courtyard (net) area matches target."""
    poly = generate_courtyard(area_m2=800.0, courtyard_fraction=0.25)
    assert poly.is_valid
    assert poly.area == pytest.approx(800.0, rel=0.02)


def test_courtyard_has_hole() -> None:
    """Courtyard polygon has an interior ring."""
    poly = generate_courtyard(area_m2=800.0)
    assert len(list(poly.interiors)) == 1


def test_t_shape_area() -> None:
    """T-shape approximates target area."""
    poly = generate_t_shape(area_m2=450.0)
    assert poly.is_valid
    assert poly.area == pytest.approx(450.0, rel=0.05)


def test_t_shape_has_8_vertices() -> None:
    """T-shape has 8 unique vertices."""
    poly = generate_t_shape(area_m2=450.0)
    assert len(poly.exterior.coords) == 9  # closed ring
