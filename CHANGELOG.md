# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added — Full-Population Rebuild (Option C Multi-pathway)

- **Full-population pipeline** (`src/murb_geometry/pipeline.py`) — processes all
  12 provinces/territories without arbitrary row caps
- **Option C multi-pathway classification** — parallel precision and tiered pathways
  with sensitivity analysis between them
- **`run-all` CLI command** — one-command full national execution
- **`preprocess` CLI command** — single-province processing
- **Evidence-based archetype module** (`archetypes/evidence_based.py`) —
  diagnostic-driven cluster count selection with silhouette, inertia, and stability
- **Output specification** (`docs/output_specification.md`) — complete research
  question → output matrix
- **Pathway sensitivity report** — quantifies how results differ between pathways
- **Classification summary CSV** — per-province breakdown by confidence level
- **GeoParquet persistence** — full processed datasets at `data/processed/`
- **Run manifest** — timings, counts, hashes, config, software versions
- **National full-run script** (`scripts/national_full_run.py`) — production runner

### Changed

- `pyproject.toml`: Python requirement relaxed to >=3.11 (was >=3.12)
- `config/default.yaml`: Added pathway, precision_levels, tiered_levels
- `src/murb_geometry/config.py`: ClassificationConfig expanded with pathway fields
- `docs/methodology.md`: Complete rewrite for Option C multi-pathway approach

### Deprecated

- `scripts/complete_run.py` — uses MAX_PER_FILE=2000 and fixed k=5/8.
  Use `murb-geometry run-all` instead.

### Fixed

- Pipeline handles pandas NaN values in classification (not just None/"..")

---

### Added (Previous)

- Complete national MURB analysis pipeline (Phases 0–8)
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
- GETTING_STARTED.md and OUTPUTS_GUIDE.md plain-language guides
- Synthetic parametric geometry generators (rectangle, L, U, T, courtyard)
- gbXML structural validator
- Complete run script with merged provinces (scripts/complete_run.py)
- Per-province analysis scripts (NS, all provinces)
- Publication figure generation script

### National Run Results (Merged Provinces)

- Inventoried 14,417,429 building records across 15 GeoPackage files (6.3 GB)
- Identified 7,567 confirmed MURBs across 5 provinces (NS, NB, ON, BC, AB)
- Ontario files (ON_1 + ON_2 + ON_3) merged as single province
- National median MURB footprint: 389 m² (IQR 214–737)
- National median aspect ratio: 1.89
- 25 per-province archetypes (5 per province via K-means)
- 8 national archetypes from combined clustering
- 32 gbXML simulation files (one per archetype per province)
- 8 publication-quality figures (PNG)

### Per-Province Highlights

- NS: 2,000 MURBs, most common = 231 m² compact (45%)
- NB: 2,000 MURBs, most common = 297 m² compact (47%)
- ON: 1,901 MURBs (3 files merged), most common = 300 m² compact (48%)
- BC: 393 MURBs, largest median (942 m²), some up to 7,575 m²
- AB: 1,273 MURBs, most common = 332 m² compact (34%)

### Outputs Committed

- outputs/reports/complete_analysis.json — Full per-province analysis
- outputs/reports/inventory.json — National file inventory
- outputs/reports/methodology_report.txt — Written methodology
- outputs/excel/complete_murb_analysis.xlsx — Main Excel report
- outputs/figures/ — 8 publication PNG figures
- outputs/gbxml/ — 32 gbXML files (per archetype per province)
- outputs/archetypes/national_archetypes.json — 8 national archetypes
