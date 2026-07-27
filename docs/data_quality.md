# Data Quality Assessment

## Principles

- Every analytical output must report data completeness
- Source-specific quality must be assessed before aggregation
- National statistics must acknowledge coverage gaps
- Outliers must be investigated, not silently removed

## Quality Dimensions

### Coverage
- Geographic: which municipalities, provinces are represented?
- Temporal: how current is each source?
- Attribute: which fields are populated?

### Completeness
Report for each field:
- Total records
- Non-missing records
- Completeness percentage
- By province
- By source organization

### Accuracy
- CRS verification
- Geometry validity
- Plausible value ranges
- Cross-field consistency

### Consistency
- Same building type terminology across sources?
- Unit count formats consistent?
- Height units consistent?

## Quality Flags

Each record should carry quality indicators:
- `has_valid_geometry`: bool
- `has_type`: bool
- `has_floors`: bool
- `has_units`: bool
- `has_height`: bool
- `has_year_built`: bool
- `attribute_completeness_score`: float (0–1)
- `geometry_quality_score`: float (0–1)

## Known Quality Issues

1. Many provinces have 0% attribute completeness for key fields
2. "Automatically Extracted Buildings" from satellite imagery have no attributes
3. Source classification systems are not interoperable
4. Storey counts from different sources may include/exclude basements differently
5. Height may represent eave height, ridge height, or average height
6. sq_ft field meaning varies (footprint? gross floor area? livable area?)
