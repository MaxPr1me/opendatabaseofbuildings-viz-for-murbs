"""gbXML serialization — export BuildingGeometryModel to gbXML XML.

Generates valid gbXML from the intermediate building geometry model.
Targets gbXML schema version 7.03.
"""

from xml.dom.minidom import parseString
from xml.etree.ElementTree import Element, SubElement, tostring

from murb_geometry.gbxml.model import (
    BuildingGeometryModel,
)


def export_gbxml(model: BuildingGeometryModel) -> str:
    """Export a BuildingGeometryModel to gbXML XML string.

    Parameters
    ----------
    model
        The building geometry model to export.

    Returns
    -------
    str
        Pretty-printed gbXML XML string.
    """
    root = Element("gbXML")
    root.set("xmlns", "http://www.gbxml.org/schema")
    root.set("temperatureUnit", "C")
    root.set("lengthUnit", "Meters")
    root.set("areaUnit", "SquareMeters")
    root.set("volumeUnit", "CubicMeters")
    root.set("version", "7.03")

    # Campus
    campus = SubElement(root, "Campus")
    campus.set("id", "Campus-1")

    # Building
    building = SubElement(campus, "Building")
    building.set("id", "Building-1")
    building.set("buildingType", "MultiFamily")

    name_el = SubElement(building, "Name")
    name_el.text = model.name

    area_el = SubElement(building, "Area")
    area_el.text = f"{model.total_floor_area_m2:.2f}"

    # Building storeys
    for storey in model.storeys:
        bs = SubElement(building, "BuildingStorey")
        bs.set("id", f"Storey-{storey.level}")
        level_el = SubElement(bs, "Level")
        level_el.text = f"{storey.elevation_m:.2f}"
        name_s = SubElement(bs, "Name")
        name_s.text = storey.name

        # Spaces
        for space in storey.spaces:
            sp = SubElement(building, "Space")
            sp.set("id", f"Space-{storey.level}-{space.name}")
            sp.set("buildingStoreyIdRef", f"Storey-{storey.level}")

            sp_name = SubElement(sp, "Name")
            sp_name.text = space.name

            sp_area = SubElement(sp, "Area")
            sp_area.text = f"{space.floor_area_m2:.2f}"

            sp_vol = SubElement(sp, "Volume")
            sp_vol.text = f"{space.volume_m3:.2f}"

    # Surfaces (at Campus level per gbXML spec)
    surface_id = 1
    for storey in model.storeys:
        for space in storey.spaces:
            for surface in space.surfaces:
                surf_el = SubElement(campus, "Surface")
                surf_el.set("id", f"Surface-{surface_id}")
                surf_el.set("surfaceType", surface.surface_type.value)

                s_name = SubElement(surf_el, "Name")
                s_name.text = surface.name

                # Adjacent space reference
                adj = SubElement(surf_el, "AdjacentSpaceId")
                adj.set("spaceIdRef", f"Space-{storey.level}-{space.name}")

                # Planar geometry
                if surface.vertices:
                    pg = SubElement(surf_el, "PlanarGeometry")
                    polyloop = SubElement(pg, "PolyLoop")
                    for v in surface.vertices:
                        cp = SubElement(polyloop, "CartesianPoint")
                        for coord in [v.x, v.y, v.z]:
                            c = SubElement(cp, "Coordinate")
                            c.text = f"{coord:.4f}"

                # Openings
                for opening in surface.openings:
                    op = SubElement(surf_el, "Opening")
                    op.set("openingType", opening.opening_type)
                    op_name = SubElement(op, "Name")
                    op_name.text = opening.name
                    if opening.vertices:
                        op_pg = SubElement(op, "PlanarGeometry")
                        op_poly = SubElement(op_pg, "PolyLoop")
                        for v in opening.vertices:
                            cp = SubElement(op_poly, "CartesianPoint")
                            for coord in [v.x, v.y, v.z]:
                                c = SubElement(cp, "Coordinate")
                                c.text = f"{coord:.4f}"

                surface_id += 1

    # Pretty print
    raw_xml = tostring(root, encoding="unicode")
    dom = parseString(raw_xml)
    return dom.toprettyxml(indent="  ", encoding=None)
