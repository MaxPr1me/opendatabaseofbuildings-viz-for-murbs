# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Repository scaffold and project structure (Phase 0)
- Comprehensive README.md with research objectives and methodology
- AGENTS.md coding agent instructions
- Python project configuration with pyproject.toml
- Configuration schema and templates (config/default.yaml)
- Documentation templates under docs/
- Source code skeleton under src/murb_geometry/
- Test structure under tests/
- Streamlit application with filters and inventory display (app/)
- Pre-commit hooks configuration
- Makefile for common development tasks
- Data directory documentation and .gitignore rules
- Phased implementation roadmap
- GeoPackage inventory module with CLI commands (Phase 1)
- Geometry metrics: area, perimeter, MRR, aspect ratio, compactness,
  rectangularity, convexity, holes, components (Phase 2)
- Geometry validation with OGC checks and make_valid repair (Phase 2)
- MURB classification engine with confidence scoring (Phase 3)
- Type normalization mapping for source-specific values (Phase 3)
- Descriptive statistics module with full percentile reporting (Phase 4)
- Excel workbook generator with formatted sheets (Phase 4)
- Enrichment framework with provenance tracking (Phase 5)
- K-means clustering with medoid archetype selection (Phase 6)
- Intermediate building geometry model for simulation (Phase 7)
- gbXML XML exporter targeting schema version 7.03 (Phase 7)
- All 12 CLI commands fully implemented (no placeholders)
- GETTING_STARTED.md plain-language guide
- National production run script (scripts/national_run.py)
- NS MURB deep analysis script (scripts/analyze_ns.py)
- Sample output generation script (scripts/generate_outputs.py)

### National Run Results

- Inventoried 14,417,429 building records across 15 GeoPackage files (6.3 GB)
- Computed geometry metrics on 7,500 sampled buildings (500 per file)
- National median building footprint: 91 m²
- Nova Scotia MURB characterization: 2,766 confirmed MURBs (units >= 4)
  - Median footprint: 346 m², IQR 176–938 m²
  - Median aspect ratio: 1.73
  - Median dwelling units: 12
- Generated 6 representative archetypes via K-means clustering
- Produced sample gbXML (NS-A05: 18.4m x 12.9m, 4-storey rectangle)

### Outputs Committed

- outputs/reports/inventory.json — National file inventory
- outputs/reports/summary_stats.json — Geometry statistics
- outputs/reports/classification_summary.json — MURB classification
- outputs/reports/ns_murb_analysis.json — NS MURB characterization
- outputs/archetypes/ns_archetypes.json — 6 archetype definitions
- outputs/excel/murb_national_summary.xlsx — Formatted Excel report
- outputs/gbxml/ns_a05_archetype.xml — Sample simulation geometry
