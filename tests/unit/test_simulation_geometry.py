"""Tests for multi-pathway simulation geometry generation."""

import pytest
from shapely.geometry import box

from murb_geometry.gbxml.exporter import export_gbxml
from murb_geometry.gbxml.simulation_geometry import (
    GeometryPathway,
    SimulationGeometrySpec,
    SimulationParameter,
    ValueStatus,
    build_from_medoid,
    build_from_rectangle,
    build_sensitivity_variants,
    generate_simulation_geometry,
)
from murb_geometry.gbxml.validator import validate_gbxml_structure


@pytest.fixture
def medoid_spec():
    """Spec for medoid extrusion pathway."""
    return SimulationGeometrySpec(
        pathway=GeometryPathway.MEDOID_EXTRUSION,
        name="NS Medoid A01",
        source_building_id="NS-12345",
        archetype_id="NS-A01",
        medoid_footprint=box(0, 0, 30, 20),
        num_storeys=SimulationParameter("storeys", 5, ValueStatus.OBSERVED, "ODB floors field"),
        floor_to_floor_m=SimulationParameter("fth", 3.0, ValueStatus.ASSUMED, "config default"),
        wwr_south=SimulationParameter("wwr_s", 0.40, ValueStatus.ASSUMED, "literature"),
        limitations=["WWR assumed, not observed"],
    )


@pytest.fixture
def rectangle_spec():
    """Spec for synthetic parametric rectangle."""
    return SimulationGeometrySpec(
        pathway=GeometryPathway.SYNTHETIC_PARAMETRIC,
        name="National Archetype NAT-A01",
        archetype_id="NAT-A01",
        footprint_area_m2=SimulationParameter(
            "area", 800.0, ValueStatus.ESTIMATED, "cluster median"
        ),
        aspect_ratio=SimulationParameter("ar", 2.5, ValueStatus.ESTIMATED, "cluster median"),
        num_storeys=SimulationParameter("storeys", 6, ValueStatus.ESTIMATED, "cluster median"),
        floor_to_floor_m=SimulationParameter("fth", 3.0, ValueStatus.ASSUMED, "config"),
        orientation_deg=SimulationParameter(
            "orient", 45.0, ValueStatus.ESTIMATED, "cluster median"
        ),
    )


class TestMedoidExtrusion:
    def test_creates_correct_storeys(self, medoid_spec):
        model = build_from_medoid(medoid_spec)
        assert model.num_storeys == 5
        assert len(model.storeys) == 5

    def test_footprint_area_from_polygon(self, medoid_spec):
        model = build_from_medoid(medoid_spec)
        assert model.footprint_area_m2 == pytest.approx(600.0)  # 30 * 20

    def test_total_floor_area(self, medoid_spec):
        model = build_from_medoid(medoid_spec)
        assert model.total_floor_area_m2 == pytest.approx(3000.0)  # 600 * 5

    def test_height(self, medoid_spec):
        model = build_from_medoid(medoid_spec)
        assert model.height_m == pytest.approx(15.0)  # 5 * 3.0

    def test_construction_method(self, medoid_spec):
        model = build_from_medoid(medoid_spec)
        assert model.construction_method == "medoid_extrusion"

    def test_has_wall_surfaces(self, medoid_spec):
        model = build_from_medoid(medoid_spec)
        walls = [
            s
            for storey in model.storeys
            for space in storey.spaces
            for s in space.surfaces
            if s.surface_type == "ExteriorWall"
        ]
        # Rectangle has 4 edges * 5 storeys = 20 walls
        assert len(walls) == 20

    def test_has_ground_and_roof(self, medoid_spec):
        model = build_from_medoid(medoid_spec)
        all_surfaces = [
            s for storey in model.storeys for space in storey.spaces for s in space.surfaces
        ]
        ground = [s for s in all_surfaces if s.surface_type == "UndergroundSlab"]
        roof = [s for s in all_surfaces if s.surface_type == "Roof"]
        assert len(ground) == 1
        assert len(roof) == 1

    def test_gbxml_export_valid(self, medoid_spec):
        model = build_from_medoid(medoid_spec)
        xml = export_gbxml(model)
        result = validate_gbxml_structure(xml)
        assert result["valid"]

    def test_requires_footprint(self):
        spec = SimulationGeometrySpec(
            pathway=GeometryPathway.MEDOID_EXTRUSION,
            name="No footprint",
        )
        with pytest.raises(ValueError, match="medoid_footprint required"):
            build_from_medoid(spec)


class TestRectangleGeometry:
    def test_area_preserved(self, rectangle_spec):
        model = build_from_rectangle(rectangle_spec)
        assert model.footprint_area_m2 == pytest.approx(800.0)

    def test_storeys_correct(self, rectangle_spec):
        model = build_from_rectangle(rectangle_spec)
        assert model.num_storeys == 6

    def test_orientation_applied(self, rectangle_spec):
        model = build_from_rectangle(rectangle_spec)
        assert model.orientation_deg == pytest.approx(45.0)

    def test_assumptions_recorded(self, rectangle_spec):
        model = build_from_rectangle(rectangle_spec)
        assert "area" in model.assumptions
        assert "estimated" in model.assumptions["area"]

    def test_wwr_defaults_assumed(self, rectangle_spec):
        model = build_from_rectangle(rectangle_spec)
        assert model.wwr_south == 0.40
        assert "assumptions" in str(model.limitations) or "assumed" in str(model.limitations)

    def test_gbxml_export_valid(self, rectangle_spec):
        model = build_from_rectangle(rectangle_spec)
        xml = export_gbxml(model)
        result = validate_gbxml_structure(xml)
        assert result["valid"]


class TestSensitivityVariants:
    def test_generates_three_variants(self, rectangle_spec):
        variants = build_sensitivity_variants(rectangle_spec)
        assert len(variants) == 3
        names = [v[0] for v in variants]
        assert "minimum" in names
        assert "central" in names
        assert "maximum" in names

    def test_minimum_smaller_than_central(self, rectangle_spec):
        variants = dict(build_sensitivity_variants(rectangle_spec))
        assert variants["minimum"].footprint_area_m2 < variants["central"].footprint_area_m2

    def test_maximum_larger_than_central(self, rectangle_spec):
        variants = dict(build_sensitivity_variants(rectangle_spec))
        assert variants["maximum"].footprint_area_m2 > variants["central"].footprint_area_m2

    def test_all_variants_valid_gbxml(self, rectangle_spec):
        variants = build_sensitivity_variants(rectangle_spec)
        for name, model in variants:
            xml = export_gbxml(model)
            result = validate_gbxml_structure(xml)
            assert result["valid"], f"Variant '{name}' produced invalid gbXML"


class TestGenerateSimulationGeometry:
    def test_routes_medoid(self, medoid_spec):
        model = generate_simulation_geometry(medoid_spec)
        assert model.construction_method == "medoid_extrusion"

    def test_routes_synthetic(self, rectangle_spec):
        model = generate_simulation_geometry(rectangle_spec)
        assert model.construction_method == "synthetic_parametric"

    def test_unknown_pathway_raises(self):
        spec = SimulationGeometrySpec(pathway="unknown", name="bad")
        with pytest.raises(ValueError, match="Unknown pathway"):
            generate_simulation_geometry(spec)
