# gbXML Design

## Purpose

Export representative MURB geometries as valid gbXML files suitable for import into OpenStudio and translation to EnergyPlus IDF.

## Status: Planned (Phase 7)

## Design Principles

1. gbXML is an engineering data exchange format, not a simple XML dump
2. Geometric validity is non-negotiable (closed surfaces, consistent normals)
3. OpenStudio compatibility requires actual import testing
4. An intermediate geometry model decouples building definition from export format

## Intermediate Building Geometry Model

Before gbXML export, buildings are represented as:

```
Site
└── Building
    ├── metadata (name, address, use, area)
    ├── BuildingStorey[] (floor-to-floor heights)
    │   └── Space[] (thermal zones)
    │       └── Surface[] (walls, floors, ceilings, roofs)
    │           ├── geometry (planar polygon, 3D coordinates)
    │           ├── type (ExteriorWall, Roof, UndergroundSlab, etc.)
    │           ├── adjacency (exterior, ground, another space)
    │           └── Opening[] (windows, doors)
    │               ├── geometry
    │               └── type
    └── coordinate_system
```

## Supported Workflows

### Export actual building
- Selected footprint → extrude by storeys × floor height
- Apply setbacks if specified
- Assign surfaces and adjacency
- Apply WWR assumptions by facade orientation

### Export synthetic archetype
- Construct from parameters (area, aspect ratio, shape, storeys)
- Do NOT average polygon coordinates from different buildings
- Use parametric generators (rectangle, L, U, courtyard, tower)

## Validation Requirements

1. XML schema validation against gbXML XSD
2. Geometric closure (all spaces fully enclosed)
3. Planar surface check
4. Consistent outward-facing normals
5. No duplicate vertices
6. No zero-area surfaces
7. Space volumes > 0
8. Adjacency consistency
9. OpenStudio import test (warning/error report)
10. Area and volume comparison (expected vs. imported)

## Future Export Formats

The intermediate model should also support:
- OpenStudio Model (.osm) — planned
- EnergyPlus IDF geometry — planned
- GeoJSON (2D footprint + metadata) — planned
- OBJ / glTF (3D visualization) — future
- SVG / DXF (plan views) — future
