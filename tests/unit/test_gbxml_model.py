"""Unit tests for gbXML building geometry model."""

from murb_geometry.gbxml.model import (
    Adjacency,
    BuildingGeometryModel,
    Space,
    Storey,
    Surface,
    SurfaceType,
    Vertex,
)


def test_building_model_creation() -> None:
    """BuildingGeometryModel can be instantiated with defaults."""
    model = BuildingGeometryModel(name="Test Building")
    assert model.name == "Test Building"
    assert model.storeys == []
    assert model.wwr_south == 0.40


def test_storey_creation() -> None:
    """Storey with spaces can be created."""
    storey = Storey(
        name="Ground Floor",
        level=0,
        floor_to_floor_m=3.5,
        elevation_m=0.0,
    )
    assert storey.floor_to_floor_m == 3.5


def test_surface_creation() -> None:
    """Surface with vertices and type."""
    surface = Surface(
        name="South Wall",
        surface_type=SurfaceType.EXTERIOR_WALL,
        adjacency=Adjacency.EXTERIOR,
        vertices=[
            Vertex(x=0, y=0, z=0),
            Vertex(x=10, y=0, z=0),
            Vertex(x=10, y=0, z=3),
            Vertex(x=0, y=0, z=3),
        ],
        area_m2=30.0,
        azimuth_deg=180.0,
    )
    assert surface.surface_type == SurfaceType.EXTERIOR_WALL
    assert len(surface.vertices) == 4


def test_full_building_model() -> None:
    """Complete building model with storey and space."""
    space = Space(
        name="Zone 1",
        floor_area_m2=200.0,
        volume_m3=600.0,
    )
    storey = Storey(
        name="Floor 1",
        level=0,
        floor_to_floor_m=3.0,
        spaces=[space],
    )
    model = BuildingGeometryModel(
        name="MURB Archetype A1",
        storeys=[storey],
        total_floor_area_m2=200.0,
        total_volume_m3=600.0,
        footprint_area_m2=200.0,
        height_m=3.0,
        num_storeys=1,
        construction_method="synthetic_parametric",
    )
    assert len(model.storeys) == 1
    assert model.storeys[0].spaces[0].floor_area_m2 == 200.0
    assert model.construction_method == "synthetic_parametric"
