"""gbXML schema validation utilities.

Validates exported gbXML against structural rules without requiring
an external XSD file download. Checks geometric validity, surface
consistency, and required elements.
"""

from xml.etree.ElementTree import fromstring


def validate_gbxml_structure(xml_string: str) -> dict[str, object]:
    """Validate a gbXML XML string for structural correctness.

    Checks:
    - Valid XML parsing
    - Root element is gbXML with correct namespace
    - Campus, Building, Space elements exist
    - Surfaces have PlanarGeometry with vertices
    - No zero-vertex surfaces
    - Building has storeys

    Parameters
    ----------
    xml_string
        The gbXML XML content as a string.

    Returns
    -------
    dict with keys:
        valid: bool — overall pass/fail
        errors: list[str] — fatal issues
        warnings: list[str] — non-fatal issues
        stats: dict — element counts
    """
    errors: list[str] = []
    warnings: list[str] = []
    stats: dict[str, int] = {}

    # Parse XML
    try:
        root = fromstring(xml_string)
    except Exception as e:
        return {"valid": False, "errors": [f"XML parse error: {e}"], "warnings": [], "stats": {}}

    # Check root element
    ns = {"gb": "http://www.gbxml.org/schema"}
    tag = root.tag
    if "gbXML" not in tag:
        errors.append(f"Root element is '{tag}', expected 'gbXML'")

    # Check version
    version = root.get("version", "")
    if not version:
        warnings.append("No version attribute on gbXML root")
    stats["version"] = version  # type: ignore[assignment]

    # Find Campus
    campuses = root.findall(".//gb:Campus", ns) or root.findall(".//Campus")
    if not campuses:
        # Try without namespace
        campuses = [el for el in root.iter() if "Campus" in el.tag]
    stats["campuses"] = len(campuses)
    if not campuses:
        errors.append("No Campus element found")

    # Find Buildings
    buildings = [el for el in root.iter() if "Building" in el.tag and "Storey" not in el.tag]
    stats["buildings"] = len(buildings)
    if not buildings:
        errors.append("No Building element found")

    # Find Storeys
    storeys = [el for el in root.iter() if "BuildingStorey" in el.tag]
    stats["storeys"] = len(storeys)
    if not storeys:
        warnings.append("No BuildingStorey elements found")

    # Find Spaces
    spaces = [el for el in root.iter() if el.tag.endswith("Space") or "}Space" in el.tag]
    stats["spaces"] = len(spaces)
    if not spaces:
        warnings.append("No Space elements found")

    # Find Surfaces
    surfaces = [el for el in root.iter() if "Surface" in el.tag and "Adj" not in el.tag]
    stats["surfaces"] = len(surfaces)
    if not surfaces:
        errors.append("No Surface elements found")

    # Check surfaces have geometry
    surfaces_with_geom = 0
    zero_vertex_surfaces = 0
    for surf in surfaces:
        poly_loops = [el for el in surf.iter() if "PolyLoop" in el.tag]
        if poly_loops:
            surfaces_with_geom += 1
            points = [el for el in poly_loops[0].iter() if "CartesianPoint" in el.tag]
            if len(points) < 3:
                zero_vertex_surfaces += 1
        else:
            warnings.append(f"Surface '{surf.get('id', '?')}' has no PlanarGeometry")

    stats["surfaces_with_geometry"] = surfaces_with_geom
    if zero_vertex_surfaces > 0:
        errors.append(f"{zero_vertex_surfaces} surfaces have fewer than 3 vertices")

    # Find Openings
    openings = [el for el in root.iter() if "Opening" in el.tag]
    stats["openings"] = len(openings)

    # Check for required attributes
    for surf in surfaces:
        surf_type = surf.get("surfaceType", "")
        if not surf_type:
            warnings.append(f"Surface '{surf.get('id', '?')}' missing surfaceType")

    valid = len(errors) == 0
    return {
        "valid": valid,
        "errors": errors,
        "warnings": warnings,
        "stats": stats,
    }
