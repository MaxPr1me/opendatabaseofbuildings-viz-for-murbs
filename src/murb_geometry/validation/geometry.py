"""Geometry validation and repair functions.

Validates building footprint geometries and provides quality flags.
Repaired geometries are returned separately — originals are never modified.
"""

from shapely import Geometry, make_valid
from shapely.geometry import MultiPolygon, Polygon
from shapely.validation import explain_validity


def validate_geometry(geom: Geometry | None) -> dict[str, bool | str | None]:
    """Validate a geometry and return quality flags.

    Parameters
    ----------
    geom
        A shapely geometry (typically Polygon or MultiPolygon).

    Returns
    -------
    dict with keys:
        is_null: geometry is None
        is_empty: geometry exists but is empty
        is_valid: OGC validity
        validity_reason: explanation if invalid (None if valid)
        is_polygon: geometry is Polygon or MultiPolygon
        has_zero_area: area == 0
        repaired: repaired geometry if invalid, else None
    """
    if geom is None:
        return {
            "is_null": True,
            "is_empty": False,
            "is_valid": False,
            "validity_reason": "NULL geometry",
            "is_polygon": False,
            "has_zero_area": True,
            "repaired": None,
        }

    if geom.is_empty:
        return {
            "is_null": False,
            "is_empty": True,
            "is_valid": False,
            "validity_reason": "Empty geometry",
            "is_polygon": False,
            "has_zero_area": True,
            "repaired": None,
        }

    is_polygon = isinstance(geom, (Polygon, MultiPolygon))
    is_valid = geom.is_valid
    validity_reason = None if is_valid else explain_validity(geom)
    has_zero_area = geom.area == 0

    repaired = None
    if not is_valid:
        try:
            repaired = make_valid(geom)
        except Exception:
            repaired = None

    return {
        "is_null": False,
        "is_empty": False,
        "is_valid": is_valid,
        "validity_reason": validity_reason,
        "is_polygon": is_polygon,
        "has_zero_area": has_zero_area,
        "repaired": repaired,
    }
