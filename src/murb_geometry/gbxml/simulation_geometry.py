"""Multi-pathway simulation geometry generation.

Supports four geometry pathways:
1. Actual medoid footprint extrusion
2. Simplified observed-shape geometry
3. Synthetic parametric archetypes (rectangle, L, U, T, courtyard)
4. Min/central/max sensitivity variants

Every parameter has explicit provenance (observed/estimated/assumed).
Geometry is NOT forced to a rectangle unless that is the configured case.
"""

import logging
import math
from dataclasses import dataclass, field
from enum import StrEnum

from shapely.geometry import Polygon

from murb_geometry.gbxml.model import (
    Adjacency,
    BuildingGeometryModel,
    Space,
    Storey,
    Surface,
    SurfaceType,
    Vertex,
)

logger = logging.getLogger(__name__)


class GeometryPathway(StrEnum):
    """Simulation geometry generation pathway."""

    MEDOID_EXTRUSION = "medoid_extrusion"
    SIMPLIFIED_SHAPE = "simplified_shape"
    SYNTHETIC_PARAMETRIC = "synthetic_parametric"
    SENSITIVITY_VARIANT = "sensitivity_variant"


class ValueStatus(StrEnum):
    """Provenance status for each parameter."""

    OBSERVED = "observed"
    DERIVED = "derived"
    ESTIMATED = "estimated"
    ASSUMED = "assumed"
    CONFIGURED = "configured"


@dataclass
class SimulationParameter:
    """A simulation parameter with provenance."""

    name: str
    value: float | int | str
    status: ValueStatus
    source: str
    uncertainty: str = ""


@dataclass
class SimulationGeometrySpec:
    """Complete specification for generating simulation geometry."""

    pathway: GeometryPathway
    name: str
    archetype_id: str = ""
    source_building_id: str = ""

    # Footprint
    footprint_area_m2: SimulationParameter | None = None
    floor_plate_area_m2: SimulationParameter | None = None
    shape_class: SimulationParameter | None = None

    # Dimensions
    length_m: SimulationParameter | None = None
    width_m: SimulationParameter | None = None
    aspect_ratio: SimulationParameter | None = None
    orientation_deg: SimulationParameter | None = None

    # Vertical
    num_storeys: SimulationParameter | None = None
    floor_to_floor_m: SimulationParameter | None = None
    total_height_m: SimulationParameter | None = None

    # WWR (never from ODB — always external/assumed)
    wwr_north: SimulationParameter | None = None
    wwr_east: SimulationParameter | None = None
    wwr_south: SimulationParameter | None = None
    wwr_west: SimulationParameter | None = None

    # Medoid footprint (for pathway 1)
    medoid_footprint: Polygon | None = None

    # Metadata
    limitations: list[str] = field(default_factory=list)


def build_from_medoid(
    spec: SimulationGeometrySpec,
) -> BuildingGeometryModel:
    """Build simulation geometry by extruding a medoid footprint.

    Pathway 1: Uses actual building footprint with observed/derived height.

    Parameters
    ----------
    spec
        Specification with medoid_footprint polygon and vertical parameters.

    Returns
    -------
    BuildingGeometryModel
    """
    if spec.medoid_footprint is None:
        msg = "medoid_footprint required for MEDOID_EXTRUSION pathway"
        raise ValueError(msg)

    footprint = spec.medoid_footprint
    storeys = int(spec.num_storeys.value) if spec.num_storeys else 4
    fth = float(spec.floor_to_floor_m.value) if spec.floor_to_floor_m else 3.0
    height = storeys * fth
    area = footprint.area

    # Extract exterior ring coordinates
    coords = list(footprint.exterior.coords[:-1])  # Remove closing duplicate

    model_storeys = []
    for i in range(storeys):
        z0 = i * fth
        z1 = (i + 1) * fth

        # Create wall surfaces from footprint edges
        surfaces: list[Surface] = []
        for j in range(len(coords)):
            p1 = coords[j]
            p2 = coords[(j + 1) % len(coords)]

            # Calculate azimuth
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            azimuth = math.degrees(math.atan2(dx, dy)) % 360
            edge_length = math.sqrt(dx * dx + dy * dy)

            surfaces.append(
                Surface(
                    name=f"Wall-F{i}-E{j}",
                    surface_type=SurfaceType.EXTERIOR_WALL,
                    vertices=[
                        Vertex(p1[0], p1[1], z0),
                        Vertex(p2[0], p2[1], z0),
                        Vertex(p2[0], p2[1], z1),
                        Vertex(p1[0], p1[1], z1),
                    ],
                    area_m2=edge_length * fth,
                    azimuth_deg=azimuth,
                )
            )

        # Ground floor
        if i == 0:
            surfaces.append(
                Surface(
                    name="Ground",
                    surface_type=SurfaceType.GROUND_FLOOR,
                    adjacency=Adjacency.GROUND,
                    vertices=[Vertex(c[0], c[1], 0) for c in coords],
                    area_m2=area,
                    tilt_deg=180.0,
                )
            )

        # Roof (top floor only)
        if i == storeys - 1:
            surfaces.append(
                Surface(
                    name="Roof",
                    surface_type=SurfaceType.ROOF,
                    adjacency=Adjacency.EXTERIOR,
                    vertices=[Vertex(c[0], c[1], z1) for c in coords],
                    area_m2=area,
                    tilt_deg=0.0,
                )
            )

        space = Space(
            name=f"Zone-F{i}",
            surfaces=surfaces,
            floor_area_m2=area,
            volume_m3=area * fth,
        )
        model_storeys.append(
            Storey(
                name=f"Floor {i + 1}", level=i, floor_to_floor_m=fth, elevation_m=z0, spaces=[space]
            )
        )

    assumptions: dict[str, str] = {}
    if spec.floor_to_floor_m:
        assumptions["floor_to_floor_m"] = (
            f"{spec.floor_to_floor_m.value} ({spec.floor_to_floor_m.status})"
        )
    if spec.num_storeys:
        assumptions["storeys"] = f"{spec.num_storeys.value} ({spec.num_storeys.status})"

    return BuildingGeometryModel(
        name=spec.name,
        storeys=model_storeys,
        total_floor_area_m2=area * storeys,
        footprint_area_m2=area,
        height_m=height,
        num_storeys=storeys,
        construction_method="medoid_extrusion",
        source_building_id=spec.source_building_id,
        archetype_id=spec.archetype_id,
        wwr_north=float(spec.wwr_north.value) if spec.wwr_north else 0.30,
        wwr_east=float(spec.wwr_east.value) if spec.wwr_east else 0.30,
        wwr_south=float(spec.wwr_south.value) if spec.wwr_south else 0.40,
        wwr_west=float(spec.wwr_west.value) if spec.wwr_west else 0.30,
        assumptions=assumptions,
        limitations=spec.limitations,
    )


def build_from_rectangle(
    spec: SimulationGeometrySpec,
) -> BuildingGeometryModel:
    """Build simulation geometry as a rectangular extrusion.

    Pathway 2/3: Simplified shape or synthetic parametric rectangle.

    Parameters
    ----------
    spec
        Specification with area, aspect ratio, storeys, orientation.

    Returns
    -------
    BuildingGeometryModel
    """
    area = float(spec.footprint_area_m2.value) if spec.footprint_area_m2 else 500.0
    ar = float(spec.aspect_ratio.value) if spec.aspect_ratio else 2.0
    storeys = int(spec.num_storeys.value) if spec.num_storeys else 4
    fth = float(spec.floor_to_floor_m.value) if spec.floor_to_floor_m else 3.0
    orientation = float(spec.orientation_deg.value) if spec.orientation_deg else 0.0

    width = math.sqrt(area / max(ar, 0.1))
    length = area / width
    height = storeys * fth

    # Apply orientation rotation
    angle_rad = math.radians(orientation)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)

    # Base rectangle corners (centered at origin)
    half_l = length / 2
    half_w = width / 2
    base_corners = [
        (-half_l, -half_w),
        (half_l, -half_w),
        (half_l, half_w),
        (-half_l, half_w),
    ]

    # Rotate
    corners = [(x * cos_a - y * sin_a, x * sin_a + y * cos_a) for x, y in base_corners]

    # Build storeys
    model_storeys = []
    for i in range(storeys):
        z0 = i * fth
        z1 = (i + 1) * fth

        surfaces: list[Surface] = []
        # Four walls
        wall_names = ["South", "East", "North", "West"]
        azimuths = [
            (180 + orientation) % 360,
            (90 + orientation) % 360,
            (0 + orientation) % 360,
            (270 + orientation) % 360,
        ]
        wall_lengths = [length, width, length, width]

        for j in range(4):
            p1 = corners[j]
            p2 = corners[(j + 1) % 4]
            surfaces.append(
                Surface(
                    name=f"{wall_names[j]}-F{i}",
                    surface_type=SurfaceType.EXTERIOR_WALL,
                    vertices=[
                        Vertex(p1[0], p1[1], z0),
                        Vertex(p2[0], p2[1], z0),
                        Vertex(p2[0], p2[1], z1),
                        Vertex(p1[0], p1[1], z1),
                    ],
                    area_m2=wall_lengths[j] * fth,
                    azimuth_deg=azimuths[j],
                )
            )

        if i == 0:
            surfaces.append(
                Surface(
                    name="Ground",
                    surface_type=SurfaceType.GROUND_FLOOR,
                    adjacency=Adjacency.GROUND,
                    vertices=[Vertex(c[0], c[1], 0) for c in corners],
                    area_m2=area,
                    tilt_deg=180.0,
                )
            )
        if i == storeys - 1:
            surfaces.append(
                Surface(
                    name="Roof",
                    surface_type=SurfaceType.ROOF,
                    adjacency=Adjacency.EXTERIOR,
                    vertices=[Vertex(c[0], c[1], z1) for c in corners],
                    area_m2=area,
                    tilt_deg=0.0,
                )
            )

        space = Space(
            name=f"Zone-F{i}", surfaces=surfaces, floor_area_m2=area, volume_m3=area * fth
        )
        model_storeys.append(
            Storey(
                name=f"Floor {i + 1}", level=i, floor_to_floor_m=fth, elevation_m=z0, spaces=[space]
            )
        )

    assumptions: dict[str, str] = {
        "shape": "rectangle (simplified or synthetic)",
    }
    if spec.footprint_area_m2:
        assumptions["area"] = f"{spec.footprint_area_m2.value} ({spec.footprint_area_m2.status})"
    if spec.aspect_ratio:
        assumptions["aspect_ratio"] = f"{spec.aspect_ratio.value} ({spec.aspect_ratio.status})"
    if spec.floor_to_floor_m:
        assumptions["floor_to_floor_m"] = (
            f"{spec.floor_to_floor_m.value} ({spec.floor_to_floor_m.status})"
        )

    return BuildingGeometryModel(
        name=spec.name,
        storeys=model_storeys,
        total_floor_area_m2=area * storeys,
        footprint_area_m2=area,
        height_m=height,
        num_storeys=storeys,
        orientation_deg=orientation,
        construction_method=spec.pathway.value,
        archetype_id=spec.archetype_id,
        wwr_north=float(spec.wwr_north.value) if spec.wwr_north else 0.30,
        wwr_east=float(spec.wwr_east.value) if spec.wwr_east else 0.30,
        wwr_south=float(spec.wwr_south.value) if spec.wwr_south else 0.40,
        wwr_west=float(spec.wwr_west.value) if spec.wwr_west else 0.30,
        assumptions=assumptions,
        limitations=spec.limitations or ["WWR values are assumptions, not observed from ODB"],
    )


def build_sensitivity_variants(
    base_spec: SimulationGeometrySpec,
) -> list[tuple[str, BuildingGeometryModel]]:
    """Generate min/central/max sensitivity variants from a base spec.

    Creates three models varying area, storeys, and WWR within P25-P75 range.

    Returns
    -------
    list of (variant_name, model) tuples
    """
    variants: list[tuple[str, BuildingGeometryModel]] = []

    base_area = float(base_spec.footprint_area_m2.value) if base_spec.footprint_area_m2 else 500.0
    base_storeys = int(base_spec.num_storeys.value) if base_spec.num_storeys else 4
    base_ar = float(base_spec.aspect_ratio.value) if base_spec.aspect_ratio else 2.0

    # Minimum case
    min_spec = SimulationGeometrySpec(
        pathway=GeometryPathway.SENSITIVITY_VARIANT,
        name=f"{base_spec.name} — Minimum",
        archetype_id=base_spec.archetype_id,
        footprint_area_m2=SimulationParameter(
            "area", base_area * 0.6, ValueStatus.ESTIMATED, "P25 estimate"
        ),
        aspect_ratio=SimulationParameter("ar", base_ar, ValueStatus.ESTIMATED, "central"),
        num_storeys=SimulationParameter(
            "storeys", max(2, base_storeys - 2), ValueStatus.ESTIMATED, "P25"
        ),
        floor_to_floor_m=base_spec.floor_to_floor_m
        or SimulationParameter("fth", 2.9, ValueStatus.ASSUMED, "config"),
        orientation_deg=base_spec.orientation_deg,
        wwr_north=SimulationParameter("wwr_n", 0.20, ValueStatus.ASSUMED, "literature minimum"),
        wwr_east=SimulationParameter("wwr_e", 0.20, ValueStatus.ASSUMED, "literature minimum"),
        wwr_south=SimulationParameter("wwr_s", 0.25, ValueStatus.ASSUMED, "literature minimum"),
        wwr_west=SimulationParameter("wwr_w", 0.20, ValueStatus.ASSUMED, "literature minimum"),
        limitations=["Sensitivity minimum — not a specific observed building"],
    )
    variants.append(("minimum", build_from_rectangle(min_spec)))

    # Central case
    central_spec = SimulationGeometrySpec(
        pathway=GeometryPathway.SENSITIVITY_VARIANT,
        name=f"{base_spec.name} — Central",
        archetype_id=base_spec.archetype_id,
        footprint_area_m2=base_spec.footprint_area_m2
        or SimulationParameter("area", base_area, ValueStatus.ESTIMATED, "median"),
        aspect_ratio=base_spec.aspect_ratio
        or SimulationParameter("ar", base_ar, ValueStatus.ESTIMATED, "median"),
        num_storeys=base_spec.num_storeys
        or SimulationParameter("storeys", base_storeys, ValueStatus.ESTIMATED, "median"),
        floor_to_floor_m=base_spec.floor_to_floor_m
        or SimulationParameter("fth", 3.0, ValueStatus.ASSUMED, "config"),
        orientation_deg=base_spec.orientation_deg,
        wwr_north=SimulationParameter("wwr_n", 0.30, ValueStatus.ASSUMED, "literature central"),
        wwr_east=SimulationParameter("wwr_e", 0.30, ValueStatus.ASSUMED, "literature central"),
        wwr_south=SimulationParameter("wwr_s", 0.40, ValueStatus.ASSUMED, "literature central"),
        wwr_west=SimulationParameter("wwr_w", 0.30, ValueStatus.ASSUMED, "literature central"),
        limitations=["Sensitivity central — archetypal assumption"],
    )
    variants.append(("central", build_from_rectangle(central_spec)))

    # Maximum case
    max_spec = SimulationGeometrySpec(
        pathway=GeometryPathway.SENSITIVITY_VARIANT,
        name=f"{base_spec.name} — Maximum",
        archetype_id=base_spec.archetype_id,
        footprint_area_m2=SimulationParameter(
            "area", base_area * 1.5, ValueStatus.ESTIMATED, "P75 estimate"
        ),
        aspect_ratio=SimulationParameter("ar", base_ar, ValueStatus.ESTIMATED, "central"),
        num_storeys=SimulationParameter("storeys", base_storeys + 4, ValueStatus.ESTIMATED, "P75"),
        floor_to_floor_m=base_spec.floor_to_floor_m
        or SimulationParameter("fth", 3.2, ValueStatus.ASSUMED, "config"),
        orientation_deg=base_spec.orientation_deg,
        wwr_north=SimulationParameter("wwr_n", 0.40, ValueStatus.ASSUMED, "literature maximum"),
        wwr_east=SimulationParameter("wwr_e", 0.40, ValueStatus.ASSUMED, "literature maximum"),
        wwr_south=SimulationParameter("wwr_s", 0.60, ValueStatus.ASSUMED, "literature maximum"),
        wwr_west=SimulationParameter("wwr_w", 0.40, ValueStatus.ASSUMED, "literature maximum"),
        limitations=["Sensitivity maximum — not a specific observed building"],
    )
    variants.append(("maximum", build_from_rectangle(max_spec)))

    return variants


def generate_simulation_geometry(
    spec: SimulationGeometrySpec,
) -> BuildingGeometryModel:
    """Route to the appropriate builder based on pathway.

    Parameters
    ----------
    spec
        Complete simulation geometry specification.

    Returns
    -------
    BuildingGeometryModel
    """
    if spec.pathway == GeometryPathway.MEDOID_EXTRUSION:
        return build_from_medoid(spec)
    elif (
        spec.pathway in (GeometryPathway.SIMPLIFIED_SHAPE, GeometryPathway.SYNTHETIC_PARAMETRIC)
        or spec.pathway == GeometryPathway.SENSITIVITY_VARIANT
    ):
        return build_from_rectangle(spec)
    else:
        msg = f"Unknown pathway: {spec.pathway}"
        raise ValueError(msg)
