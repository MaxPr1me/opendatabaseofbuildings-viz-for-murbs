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
**Status: Complete**

Deliverables:
- [x] File inventory with hashes
- [x] Layer inspection (CRS, geometry type, row count)
- [x] Schema consistency check across provinces
- [x] Source organization inventory
- [x] Field completeness matrix (province x field)
- [x] CLI commands: `inventory`, `inspect`

## Phase 2 — Geometry Metrics
**Status: Complete**

Deliverables:
- [x] Geometry validation pipeline (valid, repaired, flagged)
- [x] Footprint area, perimeter, centroid
- [x] Minimum rotated rectangle, dimensions, aspect ratio, orientation
- [x] Compactness, rectangularity, convexity
- [x] Hole and component analysis
- [x] Unit tests with synthetic polygons

## Phase 3 — MURB Classification
**Status: Complete**

Deliverables:
- [x] Type-value normalization mapping
- [x] Evidence-based classification rules with priority ordering
- [x] Confidence-scored classification engine
- [x] Configurable thresholds
- [x] Full evidence preservation (rule_id, reasoning, evidence_fields)

## Phase 4 — Visualization and Reporting
**Status: Complete**

Deliverables:
- [x] Streamlit application with tabbed interface and filters
- [x] Excel workbook generator (Data Quality, Summary, Field Dictionary)
- [x] Descriptive statistics module (full percentile reporting)
- [x] Conditional formatting and frozen panes in Excel

## Phase 5 — Enrichment
**Status: Framework Complete**

Deliverables:
- [x] Enrichment framework with provenance tracking
- [x] EnrichmentSource and EnrichmentResult dataclasses
- [ ] External source connectors (requires data access agreements)
- [ ] Height enrichment (LiDAR/NRCan — data not yet available)
- [ ] Unit count enrichment (CMHC/assessment — data not yet available)

## Phase 6 — Representative Archetypes
**Status: Complete**

Deliverables:
- [x] Medoid selection algorithm
- [x] K-means clustering with StandardScaler normalization
- [x] Per-cluster medoid (representative actual building) selection
- [x] NS archetype results: 6 archetypes from 2000 MURBs
- [ ] Synthetic parametric geometry (L, U, courtyard shapes — future)
- [ ] Uncertainty bands (future)

## Phase 7 — Simulation Geometry and gbXML
**Status: Complete**

Deliverables:
- [x] Intermediate building geometry model (format-independent)
- [x] Storey, Space, Surface, Opening dataclasses
- [x] SurfaceType and Adjacency enums
- [x] gbXML XML serializer (export_gbxml)
- [x] Sample gbXML output (NS-A05 archetype, 4-storey rectangle)
- [ ] XSD schema validation (requires gbXML XSD download)
- [ ] OpenStudio import testing (requires OpenStudio installation)

## Phase 8 — National Analytical Report
**Status: In Progress**

Deliverables:
- [x] National inventory (all 15 files, 14.4M records)
- [x] Province-level completeness matrix
- [x] Geometry metrics on all provinces (sampled)
- [x] Classification on data-rich provinces
- [x] MURB characterization (NS: median 358 m², AR 1.80, 12 units)
- [x] Archetype generation (6 clusters from NS MURBs)
- [x] Sample gbXML export
- [ ] Full national production run (complete dataset)
- [ ] Publication-quality figures
- [ ] Peer-review-ready methodology report
