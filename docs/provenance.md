# Data Provenance Model

## Principles

- Every processed record retains its full source lineage
- Original field values are never overwritten
- Processing steps are recorded in manifests
- External enrichment is tracked separately

## Provenance Fields

For every building record:

| Field | Description |
|-------|-------------|
| original_building_id | Source `id` hash |
| province_territory | Province/territory code |
| census_subdivision_id | StatCan CSD UID |
| source_organization | Organization that provided the data |
| original_dataset_name | Source dataset name |
| source_url | Original data URL (from providers CSV) |
| source_publication_date | When source was published |
| source_update_date | When source was last updated |
| statcan_version | ODB version (v3) |
| input_file_name | GeoPackage filename |
| input_layer_name | Layer within GeoPackage |
| processing_timestamp | When this record was processed |
| processing_software_version | murb-geometry version |
| processing_rule_version | Classification/normalization rule version |

## Processing Manifests

Each analytical run generates a manifest recording:
- Run identifier (UUID)
- Timestamp
- Configuration file hash
- Input file hashes
- Software version
- Python version
- Key library versions
- Output file paths and hashes
- Record counts
- Processing duration

## External Enrichment Provenance

When records are enriched with external data:
- Source name and version
- Match method (spatial join, ID match, etc.)
- Match confidence
- Date of enrichment source
- Fields added
- Records matched vs. unmatched
