# Implementation Roadmap

## Phase 0 — Repository Initiation ✅
**Status: Complete**

- [x] README.md
- [x] AGENTS.md
- [x] Repository scaffold
- [x] Python project configuration
- [x] Environment strategy (uv + pyproject.toml)
- [x] Configuration schema and templates
- [x] Documentation templates
- [x] Source code skeleton
- [x] Test structure
- [x] Issue backlog

## Phase 1 — Data Inventory and Audit
**Status: Planned**

Deliverables:
- File inventory with hashes
- Layer inspection (CRS, geometry type, row count)
- Schema consistency check across provinces
- Source organization inventory
- Field completeness matrix (province × field)
- Data provider licence compilation
- Province/source quality matrix

Acceptance criteria:
- Every GeoPackage is inventoried without loading full data
- Completeness percentages match manual spot-checks
- Source inventory is exportable

## Phase 2 — Geometry Metrics
**Status: Planned**

Deliverables:
- Geometry validation pipeline (valid, repaired, flagged)
- Footprint area, perimeter, centroid
- Minimum rotated rectangle, dimensions, aspect ratio, orientation
- Compactness, rectangularity, convexity
- Hole and component analysis
- Facade segment extraction
- GeoParquet output (partitioned)

Acceptance criteria:
- Unit tests pass for all synthetic polygon types
- Metrics match manual GIS measurements within tolerance
- Processing handles invalid geometries gracefully

## Phase 3 — MURB Classification
**Status: Planned**

Deliverables:
- Type-value normalization mapping
- Evidence-based classification rules
- Confidence-scored candidate MURB dataset
- Manual validation sample design
- False positive/negative assessment
- Classification quality report

Acceptance criteria:
- Rules are configurable and versioned
- Every classification preserves evidence
- Validation sample achieves documented precision/recall

## Phase 4 — Visualization and Reporting
**Status: Planned**

Deliverables:
- Streamlit application with filtering and maps
- Excel workbook generator
- Distribution charts (boxplots, histograms)
- Data-quality dashboard
- Source-bias inspection tools

Acceptance criteria:
- Application handles 100k+ records responsively
- Excel output is correctly formatted
- No ArcGIS dependency

## Phase 5 — Enrichment
**Status: Planned**

Deliverables:
- External source connectors
- Height enrichment (LiDAR/NRCan)
- Storey estimation from height
- Unit count enrichment (CMHC/assessment)
- Building age enrichment
- Match confidence framework

Acceptance criteria:
- Each enrichment source documented
- Match rates reported
- Provenance preserved

## Phase 6 — Representative Archetypes
**Status: Planned**

Deliverables:
- Stratified distributions
- K-means and alternative clustering
- Medoid selection
- Synthetic parametric geometry construction
- Uncertainty bands
- Recommended simulation geometry set

Acceptance criteria:
- Multiple methods compared
- No raw polygon coordinate averaging
- Archetypes have documented uncertainty

## Phase 7 — Simulation Geometry and gbXML
**Status: Planned**

Deliverables:
- Intermediate building geometry model
- gbXML generator
- Schema validation
- OpenStudio import testing
- Geometry preview visualization

Acceptance criteria:
- Valid gbXML per XSD
- OpenStudio imports without fatal errors
- Area/volume match within 1%

## Phase 8 — National Analytical Report
**Status: Planned**

Deliverables:
- National MURB geometry characterization
- Regional findings
- Data-quality caveats
- Representative archetype recommendations
- Simulation parameter ranges
- Publication-quality figures

Acceptance criteria:
- Fully reproducible from configuration + data
- All limitations documented
- Peer-review ready
