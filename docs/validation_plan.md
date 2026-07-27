# Validation Plan

## Unit Test Validation

### Geometry Metrics
Test against synthetic polygons with known properties:
- Square (10×10): area=100, perimeter=40, aspect_ratio=1.0, compactness=π/4
- Rectangle (20×5): area=100, aspect_ratio=4.0
- Rotated rectangle: verify orientation calculation
- L-shape: verify vertex count, component handling
- Polygon with hole: verify hole_count, hole_area

### Shape Classification
- Known shapes assigned correct class
- Edge cases documented
- Confidence scores decrease for ambiguous shapes

### Classification Rules
- Each rule tested with matching and non-matching records
- Priority order verified
- Missing-data handling verified

## Integration Validation

### Pipeline Tests
- Read small GeoPackage fixture → metrics → summary → Excel
- Verify round-trip data preservation
- Verify provenance completeness

### gbXML Validation
- Generated XML passes schema validation
- OpenStudio can import without fatal errors
- Floor areas match within tolerance

## Manual Validation

### Stratified Sample Review
- Select N buildings per shape class per province
- Human reviewer confirms classification
- Calculate precision, recall, F1 per class
- Document false positive and false negative patterns

### Archetype Plausibility
- Compare archetype dimensions to known buildings
- Verify synthetic geometry looks reasonable in 3D
- Check that exported models produce plausible simulation results

## Data Validation

### Source Data Checks
- Unique IDs (no duplicates within a file)
- Valid CRS (EPSG:3347)
- No negative areas
- Storey counts > 0 where present
- Heights > 0 where present
- Units > 0 where present

### Cross-Source Consistency
- Same building from overlapping sources should be similar
- Flag large discrepancies for investigation
