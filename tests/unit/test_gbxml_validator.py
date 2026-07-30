"""Unit tests for gbXML structural validation."""

from pathlib import Path

from murb_geometry.gbxml.validator import (
    validate_gbxml,
    validate_gbxml_against_xsd,
    validate_gbxml_structure,
)


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


def test_validate_gbxml_no_xsd_reports_not_performed() -> None:
    """validate_gbxml without an XSD path runs structural checks only."""
    xml = '<?xml version="1.0" ?><gbXML xmlns="http://www.gbxml.org/schema"></gbXML>'
    result = validate_gbxml(xml)
    assert "xsd" in result
    assert result["xsd"]["xsd_available"] is False
    assert result["xsd"]["valid"] is None


def test_validate_against_missing_xsd(tmp_path) -> None:
    """A missing XSD file is reported, not raised."""
    result = validate_gbxml_against_xsd("<root/>", tmp_path / "nope.xsd")
    assert result["xsd_available"] is False
    assert result["valid"] is None


def test_validate_against_xsd_pass_and_fail(tmp_path) -> None:
    """lxml XSD validation reports pass and fail against a minimal schema."""
    xsd = tmp_path / "mini.xsd"
    xsd.write_text(
        '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
        '<xs:element name="root"><xs:complexType><xs:sequence>'
        '<xs:element name="child" type="xs:string"/>'
        "</xs:sequence></xs:complexType></xs:element></xs:schema>",
        encoding="utf-8",
    )
    ok = validate_gbxml_against_xsd("<root><child>x</child></root>", xsd)
    assert ok["xsd_available"] is True
    assert ok["valid"] is True
    assert ok["errors"] == []

    bad = validate_gbxml_against_xsd("<root><wrong/></root>", xsd)
    assert bad["xsd_available"] is True
    assert bad["valid"] is False
    assert len(bad["errors"]) > 0
