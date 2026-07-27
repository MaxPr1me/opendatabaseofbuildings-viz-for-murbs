"""gbXML export module — simulation geometry generation and validation.

Provides an intermediate building geometry model and gbXML XML generation
for export to OpenStudio and EnergyPlus.
"""

from murb_geometry.gbxml.model import BuildingGeometryModel, Storey, Surface

__all__ = ["BuildingGeometryModel", "Storey", "Surface"]
