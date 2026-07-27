# Data Dictionary

## Source Fields (ODB v3 GeoPackage)

| Field | Type | Description | Completeness |
|-------|------|-------------|--------------|
| fid | INTEGER | Row identifier (auto-increment) | 100% |
| geom | POLYGON | Building footprint in EPSG:3347 | 100% |
| id | TEXT | SHA-256 hash building identifier | 100% |
| source_id | TEXT | UUID linking to source record | 100% |
| source | TEXT | Source organization name | 100% |
| dataset | TEXT | Source dataset name | 100% |
| csduid | TEXT | Census Subdivision Unique Identifier | 100% |
| csdname | TEXT | Census Subdivision name | 100% |
| prov_terr | TEXT | Province or territory 2-letter code | 100% |
| name | TEXT | Building name | Very sparse |
| type | TEXT | Building type/use (source-specific) | 0–95% |
| address | TEXT | Street address | Varies |
| year_built | TEXT | Year of construction | Very sparse |
| units | TEXT | Number of dwelling units | 0–23% |
| floors | TEXT | Number of storeys | 0–9% |
| sq_ft | TEXT | Building area in square feet | Sparse |
| height | TEXT | Building height | 0–27% |

## Derived Fields (Calculated)

| Field | Type | Unit | Description |
|-------|------|------|-------------|
| footprint_area_m2 | FLOAT | m² | Polygon area in projected CRS |
| perimeter_m | FLOAT | m | Polygon perimeter |
| mrr_length_m | FLOAT | m | Minimum rotated rectangle major axis |
| mrr_width_m | FLOAT | m | Minimum rotated rectangle minor axis |
| aspect_ratio | FLOAT | — | mrr_length / mrr_width |
| orientation_deg | FLOAT | degrees | Major axis azimuth from north |
| compactness | FLOAT | — | 4π × area / perimeter² (Polsby-Popper) |
| rectangularity | FLOAT | — | area / mrr_area |
| convexity | FLOAT | — | area / convex_hull_area |
| hole_count | INT | — | Number of interior rings |
| component_count | INT | — | Number of disconnected parts |

## Normalized Fields

| Field | Type | Description |
|-------|------|-------------|
| type_normalized | TEXT | Standardized building-use category |
| units_numeric | INT | Parsed numeric unit count |
| floors_numeric | INT | Parsed numeric storey count |
| height_numeric | FLOAT | Parsed numeric height (m) |
| year_built_numeric | INT | Parsed construction year |

## Missing Values

Source missing values are encoded as `..` (two periods) in the original GeoPackage.
After normalization, missing values are represented as `null` / `None`.
