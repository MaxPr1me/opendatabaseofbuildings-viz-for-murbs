"""Unit tests for gbXML export."""

from murb_geometry.gbxml.exporter import export_gbxml
from murb_geometry.gbxml.model import (
    Adjacency,
    BuildingGeometryModel,
    Opening,
    Space,
    Storey,
    Surface,
    SurfaceType,
    Vertex,
)


def test_export_simple_box() -> None:
    """Export a simple box building to gbXML."""
    # Create a simple 10x20x3m box
    south_wall = Surface(
        name="South Wall",
        surface_type=SurfaceType.EXTERIOR_WALL,
        adjacency=Adjacency.EXTERIOR,
        vertices=[
            Vertex(0, 0, 0),
            Vertex(20, 0, 0),
            Vertex(20, 0, 3),
            Vertex(0, 0, 3),
        ],
        area_m2=60.0,
        azimuth_deg=180.0,
    )
    floor = Surface(
        name="Ground Floor",
        surface_type=SurfaceType.GROUND_FLOOR,
        adjacency=Adjacency.GROUND,
        vertices=[
            Vertex(0, 0, 0),
            Vertex(20, 0, 0),
            Vertex(20, 10, 0),
            Vertex(0, 10, 0),
        ],
        area_m2=200.0,
    )
    space = Space(
        name="Zone1",
        surfaces=[south_wall, floor],
        floor_area_m2=200.0,
        volume_m3=600.0,
    )
    storey = Storey(
        name="Ground Floor",
        level=0,
        floor_to_floor_m=3.0,
        spaces=[space],
    )
    model = BuildingGeometryModel(
        name="Test Box Building",
        storeys=[storey],
        total_floor_area_m2=200.0,
        total_volume_m3=600.0,
        footprint_area_m2=200.0,
        height_m=3.0,
        num_storeys=1,
    )

    xml = export_gbxml(model)

    assert '<?xml version="1.0" ?>' in xml
    assert "gbXML" in xml
    assert 'version="7.03"' in xml
    assert "Test Box Building" in xml
    assert "ExteriorWall" in xml
    assert "UndergroundSlab" in xml
    assert "CartesianPoint" in xml
    assert "200.00" in xml  # floor area


def test_export_with_opening() -> None:
    """Export a surface with a window opening."""
    window = Opening(
        name="South Window",
        opening_type="OperableWindow",
        vertices=[
            Vertex(2, 0, 0.8),
            Vertex(8, 0, 0.8),
            Vertex(8, 0, 2.4),
            Vertex(2, 0, 2.4),
        ],
    )
    wall = Surface(
        name="South Wall",
        surface_type=SurfaceType.EXTERIOR_WALL,
        adjacency=Adjacency.EXTERIOR,
        vertices=[
            Vertex(0, 0, 0),
            Vertex(10, 0, 0),
            Vertex(10, 0, 3),
            Vertex(0, 0, 3),
        ],
        openings=[window],
        area_m2=30.0,
    )
    space = Space(name="Z1", surfaces=[wall], floor_area_m2=100.0, volume_m3=300.0)
    storey = Storey(name="Floor 1", level=0, floor_to_floor_m=3.0, spaces=[space])
    model = BuildingGeometryModel(
        name="Building with Window",
        storeys=[storey],
        total_floor_area_m2=100.0,
    )

    xml = export_gbxml(model)
    assert "Opening" in xml
    assert "OperableWindow" in xml
    assert "South Window" in xml
