"""Unit tests for geometry validation."""

from shapely.geometry import LineString, MultiPolygon, Polygon

from murb_geometry.validation.geometry import validate_geometry


def test_validate_valid_polygon() -> None:
    """Valid polygon passes validation."""
    geom = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    result = validate_geometry(geom)
    assert result["is_null"] is False
    assert result["is_empty"] is False
    assert result["is_valid"] is True
    assert result["validity_reason"] is None
    assert result["is_polygon"] is True
    assert result["has_zero_area"] is False
    assert result["repaired"] is None


def test_validate_null_geometry() -> None:
    """None geometry returns null flags."""
    result = validate_geometry(None)
    assert result["is_null"] is True
    assert result["is_valid"] is False


def test_validate_empty_polygon() -> None:
    """Empty polygon is detected."""
    result = validate_geometry(Polygon())
    assert result["is_empty"] is True
    assert result["is_valid"] is False


def test_validate_bowtie_polygon() -> None:
    """Self-intersecting (bowtie) polygon is detected and repaired."""
    # Bowtie: edges cross
    geom = Polygon([(0, 0), (10, 10), (10, 0), (0, 10)])
    result = validate_geometry(geom)
    assert result["is_valid"] is False
    assert result["validity_reason"] is not None
    assert result["repaired"] is not None
    assert result["repaired"].is_valid


def test_validate_non_polygon() -> None:
    """Non-polygon geometry is flagged."""
    geom = LineString([(0, 0), (10, 10)])
    result = validate_geometry(geom)
    assert result["is_polygon"] is False
    assert result["has_zero_area"] is True


def test_validate_multipolygon() -> None:
    """Valid MultiPolygon passes."""
    geom = MultiPolygon(
        [
            Polygon([(0, 0), (5, 0), (5, 5), (0, 5)]),
            Polygon([(10, 10), (15, 10), (15, 15), (10, 15)]),
        ]
    )
    result = validate_geometry(geom)
    assert result["is_valid"] is True
    assert result["is_polygon"] is True
