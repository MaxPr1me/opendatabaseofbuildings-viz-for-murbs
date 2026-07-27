# Data Directory

This directory contains the Statistics Canada Open Database of Buildings (ODB v3)
GeoPackage files and associated metadata.

## Structure

```
data/
├── README.md              ← This file
├── ODB_v3_AB/             ← Alberta
│   ├── ODB_v3_AB.gpkg
│   └── ODB_v3_data_providers.csv
├── ODB_v3_BC/             ← British Columbia
├── ODB_v3_MB/             ← Manitoba
├── ODB_v3_NB/             ← New Brunswick
├── ODB_v3_NL/             ← Newfoundland and Labrador
├── ODB_v3_NS/             ← Nova Scotia
├── ODB_v3_NT/             ← Northwest Territories
├── ODB_v3_ON_1/           ← Ontario (part 1 of 3)
├── ODB_v3_ON_2/           ← Ontario (part 2 of 3)
├── ODB_v3_ON_3/           ← Ontario (part 3 of 3)
├── ODB_v3_PE/             ← Prince Edward Island
├── ODB_v3_QC_1/           ← Quebec (part 1 of 2)
├── ODB_v3_QC_2/           ← Quebec (part 2 of 2)
├── ODB_v3_SK/             ← Saskatchewan
├── ODB_v3_YT/             ← Yukon
├── raw/                   ← Other raw downloads (not committed)
├── external/              ← External enrichment data (not committed)
├── interim/               ← Intermediate processed data (not committed)
├── processed/             ← Final processed outputs (not committed)
└── samples/               ← Small sample subsets for development
```

## Data Inventory (ODB v3)

| File | Province | Records | Type % | Floors % | Units % | Height % | Size (MB) |
|------|----------|---------|--------|----------|---------|----------|-----------|
| ODB_v3_AB.gpkg | Alberta | 1,334,404 | 38.5% | 0.2% | 0.0% | 10.6% | 572 |
| ODB_v3_BC.gpkg | British Columbia | 1,303,603 | 11.4% | 3.2% | 0.0% | 26.5% | 618 |
| ODB_v3_MB.gpkg | Manitoba | 656,775 | 0.0% | 0.0% | 0.0% | 0.0% | 299 |
| ODB_v3_NB.gpkg | New Brunswick | 661,827 | 17.8% | 0.2% | 8.0% | 3.3% | 257 |
| ODB_v3_NL.gpkg | Newfoundland & Labrador | 187,694 | 0.0% | 0.0% | 0.0% | 0.0% | 75 |
| ODB_v3_NS.gpkg | Nova Scotia | 528,307 | 25.0% | 0.8% | 23.0% | 0.0% | 227 |
| ODB_v3_NT.gpkg | Northwest Territories | 11,811 | 94.9% | 0.0% | 0.0% | 0.0% | 5 |
| ODB_v3_ON_1.gpkg | Ontario (1/3) | 2,000,000 | 5.4% | 3.1% | 0.0% | 14.9% | 890 |
| ODB_v3_ON_2.gpkg | Ontario (2/3) | 2,000,000 | 12.2% | 8.9% | 1.7% | 16.9% | 920 |
| ODB_v3_ON_3.gpkg | Ontario (3/3) | 1,695,485 | 25.6% | 5.6% | 1.1% | 3.9% | 713 |
| ODB_v3_PE.gpkg | Prince Edward Island | 85,856 | 0.0% | 0.0% | 0.0% | 0.0% | 35 |
| ODB_v3_QC_1.gpkg | Quebec (1/2) | 2,000,000 | 16.7% | 0.0% | 0.0% | 0.0% | 862 |
| ODB_v3_QC_2.gpkg | Quebec (2/2) | 1,679,721 | 5.2% | 0.0% | 0.0% | 0.0% | 747 |
| ODB_v3_SK.gpkg | Saskatchewan | 259,461 | 0.1% | 0.0% | 0.0% | 0.0% | 116 |
| ODB_v3_YT.gpkg | Yukon | 12,485 | 0.0% | 0.0% | 0.0% | 0.0% | 5 |
| **Total** | | **14,417,429** | | | | | **~6,340** |

## Schema

All GeoPackage files share this schema:

| Field | Type | Description |
|-------|------|-------------|
| fid | INTEGER | Auto-increment row ID |
| geom | POLYGON | Building footprint (EPSG:3347) |
| id | TEXT | Unique building hash |
| source_id | TEXT | UUID linking to source record |
| source | TEXT | Source organization |
| dataset | TEXT | Source dataset name |
| csduid | TEXT | Census Subdivision UID |
| csdname | TEXT | Census Subdivision name |
| prov_terr | TEXT | Province/territory code |
| name | TEXT | Building name (sparse) |
| type | TEXT | Building type (source-specific) |
| address | TEXT | Street address |
| year_built | TEXT | Construction year |
| units | TEXT | Dwelling unit count |
| floors | TEXT | Storey count |
| sq_ft | TEXT | Area in square feet |
| height | TEXT | Building height |

Missing values are encoded as `..` (two periods).

## Important Notes

- **Do not commit GeoPackage files to Git** — they are too large (6+ GB total)
- CRS is EPSG:3347 (NAD83 / Statistics Canada Lambert) — suitable for area calculations
- All attribute fields are stored as TEXT, requiring careful parsing
- Completeness varies dramatically by province and source
- The `ODB_v3_data_providers.csv` in each folder documents source licensing

## Licence

Statistics Canada Open Database of Buildings is released under the
[Open Government Licence - Canada](https://open.canada.ca/en/open-government-licence-canada).

Individual source datasets may have additional attribution requirements
documented in `ODB_v3_data_providers.csv`.
