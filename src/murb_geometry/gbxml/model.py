"""Intermediate building geometry model for simulation export.

Format-independent representation of building geometry that can be
exported to gbXML, OSM, IDF, or visualization formats.
"""

from dataclasses import dataclass, field
from enum import StrEnum


class SurfaceType(StrEnum):
    """Building surface types for simulation."""

    EXTERIOR_WALL = "ExteriorWall"
    INTERIOR_WALL = "InteriorWall"
    ROOF = "Roof"
    FLOOR = "InteriorFloor"
    GROUND_FLOOR = "UndergroundSlab"
    CEILING = "Ceiling"


class Adjacency(StrEnum):
    """Surface adjacency conditions."""

    EXTERIOR = "Exterior"
    GROUND = "Ground"
    INTERIOR = "Interior"
    ADIABATIC = "Adiabatic"


@dataclass
class Vertex:
    """3D vertex coordinate in metres."""

    x: float
    y: float
    z: float


@dataclass
class Opening:
    """Window or door opening in a surface."""

    name: str
    opening_type: str = "OperableWindow"
    vertices: list[Vertex] = field(default_factory=list)
    wwr: float | None = None  # if specified, auto-generate from surface


@dataclass
class Surface:
    """A planar building surface."""

    name: str
    surface_type: SurfaceType
    adjacency: Adjacency = Adjacency.EXTERIOR
    vertices: list[Vertex] = field(default_factory=list)
    openings: list[Opening] = field(default_factory=list)
    adjacent_space: str | None = None
    area_m2: float = 0.0
    azimuth_deg: float = 0.0
    tilt_deg: float = 90.0


@dataclass
class Space:
    """A thermal zone or room within a storey."""

    name: str
    surfaces: list[Surface] = field(default_factory=list)
    volume_m3: float = 0.0
    floor_area_m2: float = 0.0


@dataclass
class Storey:
    """A building storey with floor-to-floor height."""

    name: str
    level: int  # 0-indexed from ground
    floor_to_floor_m: float = 3.0
    elevation_m: float = 0.0
    spaces: list[Space] = field(default_factory=list)


@dataclass
class BuildingGeometryModel:
    """Format-independent building geometry representation.

    This intermediate model can be exported to:
    - gbXML (.xml)
    - OpenStudio Model (.osm) — planned
    - EnergyPlus IDF — planned
    - GeoJSON (2D) — planned
    - OBJ / glTF (3D) — future
    """

    name: str
    storeys: list[Storey] = field(default_factory=list)
    total_floor_area_m2: float = 0.0
    total_volume_m3: float = 0.0
    footprint_area_m2: float = 0.0
    height_m: float = 0.0
    orientation_deg: float = 0.0
    num_storeys: int = 0
    construction_method: str = ""  # "actual_selected", "synthetic_parametric"
    source_building_id: str | None = None
    archetype_id: str | None = None

    # WWR assumptions by facade
    wwr_north: float = 0.30
    wwr_east: float = 0.30
    wwr_south: float = 0.40
    wwr_west: float = 0.30

    # Metadata
    assumptions: dict[str, str] = field(default_factory=dict)
    limitations: list[str] = field(default_factory=list)
