"""Unit tests for gbXML structural validation."""

from pathlib import Path

from murb_geometry.gbxml.validator import validate_gbxml_structure


def test_validate_valid_gbxml() -> None:
    """Valid gbXML passes validation."""
    xml = """<?xml version="1.0" ?>
    <gbXML xmlns="http://www.gbxml.org/schema" version="7.03">
      <Campus id="C1">
        <Building id="B1" buildingType="MultiFamily">
          <BuildingStorey id="S1"><Level>0</Level></BuildingStorey>
          <Space id="Sp1" buildingStoreyIdRef="S1"><Area>100</Area></Space>
        </Building>
        <Surface id="Surf1" surfaceType="ExteriorWall">
          <PlanarGeometry><PolyLoop>
            <CartesianPoint><Coordinate>0</Coordinate><Coordinate>0</Coordinate><Coordinate>0</Coordinate></CartesianPoint>
            <CartesianPoint><Coordinate>10</Coordinate><Coordinate>0</Coordinate><Coordinate>0</Coordinate></CartesianPoint>
            <CartesianPoint><Coordinate>10</Coordinate><Coordinate>0</Coordinate><Coordinate>3</Coordinate></CartesianPoint>
          </PolyLoop></PlanarGeometry>
        </Surface>
      </Campus>
    </gbXML>"""
    result = validate_gbxml_structure(xml)
    assert result["valid"] is True
    assert len(result["errors"]) == 0


def test_validate_invalid_xml() -> None:
    """Invalid XML fails parsing."""
    result = validate_gbxml_structure("<not valid xml>>")
    assert result["valid"] is False
    assert any("parse error" in e.lower() for e in result["errors"])


def test_validate_missing_campus() -> None:
    """Missing Campus element is an error."""
    xml = '<?xml version="1.0" ?><gbXML xmlns="http://www.gbxml.org/schema"></gbXML>'
    result = validate_gbxml_structure(xml)
    assert result["valid"] is False
    assert any("Campus" in e for e in result["errors"])


def test_validate_actual_output() -> None:
    """Validate the committed NS-A05 gbXML output."""
    gbxml_path = Path("outputs/gbxml/ns_a05_archetype.xml")
    if not gbxml_path.exists():
        return  # skip if not generated
    xml = gbxml_path.read_text(encoding="utf-8")
    result = validate_gbxml_structure(xml)
    assert result["valid"] is True
    assert result["stats"]["surfaces"] > 0
    assert result["stats"]["storeys"] > 0
