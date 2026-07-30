"""gbXML export module — simulation geometry generation and validation.

Provides an intermediate building geometry model and gbXML XML generation
for export to OpenStudio and EnergyPlus.
"""

from murb_geometry.gbxml.model import BuildingGeometryModel, Storey, Surface
from murb_geometry.gbxml.validator import (
    validate_gbxml,
    validate_gbxml_against_xsd,
    validate_gbxml_structure,
)

__all__ = [
    "BuildingGeometryModel",
    "Storey",
    "Surface",
    "validate_gbxml",
    "validate_gbxml_against_xsd",
    "validate_gbxml_structure",
]
