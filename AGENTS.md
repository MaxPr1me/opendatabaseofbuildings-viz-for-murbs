# AGENTS.md — Coding Agent Instructions

> **This is the controlling instruction document for all coding agents working in this repository.**
> Read this document in full before making any changes.

---

## 1. Project Mission

This repository develops a reproducible national workflow to characterize representative Canadian **Multi-Unit Residential Building (MURB)** geometries from the Statistics Canada Open Database of Buildings, supporting building-performance simulations with OpenStudio and EnergyPlus.

**Intended users:** Building-science researchers, energy modellers, housing-policy analysts, and simulation engineers who need defensible, data-driven building geometry inputs.

**Primary outputs:** Representative MURB geometry parameters, formatted Excel reports, interactive visualizations, and future gbXML simulation files.

---

## 2. Agent Operating Principles

Before making any change, agents **must**:

1. Read `README.md`, this `AGENTS.md`, and relevant documentation under `docs/`
2. Check existing GitHub issues for context
3. Inspect existing code in the relevant modules before proposing changes
4. Make small, reviewable, atomic changes (one logical unit per commit)
5. Preserve backward compatibility where practical

Agents **must always**:

- Use typed Python (type annotations on all public functions)
- Add or update tests for any new logic
- Document assumptions explicitly (in code comments and documentation)
- Avoid silent data transformations — every transformation must be traceable
- Preserve data provenance at every stage
- Report uncertainty alongside any statistical result
- Distinguish observed values from calculated, estimated, and assumed values

Agents **must never**:

- Commit raw national GeoPackage datasets to Git
- Introduce proprietary dependencies (ArcGIS, QGIS as runtime requirements)
- Invent data or fabricate statistical results
- Present estimates as observations
- Make national claims from geographically biased subsets without noting the bias
- Average polygon coordinates from unrelated buildings
- Hard-code absolute file paths
- Remove existing tests without justification
- Bypass linting or type-checking without documented exception
- Silently infer that large footprints are MURBs without evidence

---

## 3. Required Workflow

For each substantive task, follow this sequence:

1. **Restate the objective** — What specifically needs to be accomplished?
2. **Identify relevant modules and documents** — Which files are affected?
3. **Inspect existing implementation** — Read current code before writing new code
4. **Identify data and methodological risks** — What could go wrong? What assumptions are made?
5. **Propose an implementation plan** — Outline the approach before coding
6. **Create or reference a GitHub issue** — Every non-trivial change ties to an issue
7. **Implement the smallest coherent change** — Don't bundle unrelated changes
8. **Add tests** — Unit tests for logic, integration tests for pipelines
9. **Update documentation** — README, docs/, docstrings, CHANGELOG
10. **Run quality checks** — `make lint`, `make typecheck`, `make test`
11. **Summarize changes and limitations** — Clear PR description

---

## 4. Coding Standards

### Language and Style

- Python 3.12+ with modern syntax (`match`, `|` union types, etc.)
- Type hints on all public function signatures
- Docstrings (Google style) for all public classes and functions
- Clear function boundaries — each function does one thing
- Pure functions where practical (no side effects, deterministic)
- Maximum line length: 100 characters (enforced by ruff)

### Configuration

- **Never hard-code** research thresholds, file paths, or analytical decisions
- All configurable values in `config/default.yaml`
- Access configuration through `murb_geometry.config.load_config()`
- Use pydantic models for validated configuration

### Error Handling

- Explicit exceptions with informative messages
- No broad bare `except:` clauses
- Use specific exception types
- Log warnings for recoverable issues; raise for unrecoverable ones
- Validate inputs at module boundaries

### Logging

- Use `murb_geometry.logging.setup_logging()`
- Structured log messages
- INFO: Major pipeline steps and progress
- WARNING: Data quality issues, fallback behavior
- DEBUG: Detailed processing information
- ERROR: Failures requiring attention

### Performance

- Vectorized geospatial operations (geopandas/shapely) — avoid Python loops over geometries
- Memory-conscious processing — province-by-province, not all-at-once
- Column projection — read only needed fields from GeoPackage
- Spatial indexing for spatial operations
- Deterministic results regardless of processing order

### Code Organization

- Source-specific transformations isolated from generic processing
- One module per pipeline stage
- Shared utilities in appropriate submodules
- No circular imports
- Minimal module-level side effects

---

## 5. Geospatial Rules

### CRS Requirements

- **Verify CRS before any area or length calculation**
- Reject geographic CRS (lat/lon) for metric calculations — reproject first
- Default projected CRS: EPSG:3347 (NAD83 / Statistics Canada Lambert)
- Document CRS in all geospatial function docstrings

### Geometry Handling

- Preserve original source geometry unchanged
- Store repaired/modified geometry in separate fields
- Document all geometry repair methods
- Track invalid and empty geometries (don't silently drop them)
- Avoid unnecessary topology modification
- Preserve multipart information (don't silently explode MultiPolygons without tracking)
- Use spatial indexes for spatial queries

### Calculations

- All areas in square metres (m²)
- All lengths/perimeters in metres (m)
- All angles in degrees from north (clockwise azimuth)
- Validate units in tests (known synthetic polygons)
- Document formulas mathematically in docstrings

### Memory

- Never load all national data into memory simultaneously
- Process province-by-province
- Use pyogrio column projection and spatial filtering
- Stream large datasets where possible

---

## 6. Statistical Rules

- **Always report sample size** alongside any statistic
- **Always report missingness** (how many records lacked the field)
- **Check for outliers** before computing descriptive statistics
- Distinguish **descriptive** statistics from **inferential** statistics
- Document **weighting** when used; provide both weighted and unweighted results
- **Avoid arbitrary removal** of extreme values — document exclusion criteria
- Use **stratification** where national aggregation would obscure source bias
- Preserve **reproducible random seeds** (default: 42)
- **Validate clustering stability** (multiple runs, silhouette scores)
- Report at minimum: count, valid count, missingness, min, max, mean, median, std, P5, P10, P25, P75, P90, P95, IQR

---

## 7. Simulation Rules

### Geometry Distinctions

- **Footprint ≠ floor plate** — Ground footprint may differ from upper floors
- **Floor plate ≠ gross floor area** — GFA = floor plate × storeys (approximately)
- **Actual representative ≠ synthetic average** — These are fundamentally different
- **Never directly average polygon vertices** from unrelated buildings

### Archetype Construction

A synthetic average building must be constructed from **meaningful parameters**:
- Target floor-plate area
- Target aspect ratio
- Target shape class
- Target storeys
- Target orientation
- Target perimeter complexity

Not from averaged coordinate arrays.

### Documentation Requirements

For every archetype or simulation geometry, document:
- Source population and filters
- Selection or generation method
- Simplifications applied
- Whether party walls are known or assumed
- Orientation preservation
- Uncertainty range

---

## 8. gbXML Rules

- Treat gbXML export as an **engineering data exchange task**, not simple XML serialization
- Validate against a **documented gbXML schema version** (currently targeting 7.03)
- Create **valid closed planar surfaces** with consistent outward normals
- Distinguish surface types: exterior walls, roofs, floors, ground, interior
- Identify **adjacency** between spaces
- Create **storeys and spaces explicitly** (not implied)
- Document all assumptions: floor-to-floor height, roof geometry, ground surfaces
- Support **validation reports** stored alongside exported files
- **Never claim OpenStudio compatibility** without an actual import validation test
- Test that imported area and volume match expected values within tolerance

---

## 9. Documentation Rules

Every new feature or change must update:

- [ ] Relevant user documentation (if user-facing)
- [ ] Relevant developer documentation (if internal API changes)
- [ ] Configuration examples (if new config options)
- [ ] CHANGELOG.md
- [ ] Methodology notes in `docs/methodology.md` (if analytical meaning changes)
- [ ] Data dictionary in `docs/data_dictionary.md` (if new fields)
- [ ] Limitations in `docs/limitations.md` (if new constraints discovered)

---

## 10. Completion Criteria

**No task is complete unless:**

- [ ] Tests pass (`make test`)
- [ ] Linting passes (`make lint`)
- [ ] Type checking passes or known exceptions are documented (`make typecheck`)
- [ ] Documentation is updated
- [ ] Assumptions are explicit in code and documentation
- [ ] Outputs are reproducible (same inputs + config = same outputs)
- [ ] Data provenance is preserved (original values retained)
- [ ] Limitations are stated
- [ ] CHANGELOG is updated

---

## 11. Data Source Rules

### Primary Source

- Statistics Canada Open Database of Buildings v3
- Licence: Open Government Licence — Canada
- ~14.4 million records, 15 GeoPackage files, ~6.3 GB
- CRS: EPSG:3347
- Missing values encoded as `..`
- All attributes stored as TEXT (require parsing)

### Acceptable Enrichment Sources

- Official government publications (federal, provincial, municipal)
- Official utility data where publicly available
- Recognized Canadian standards (NBC, provincial codes)
- Peer-reviewed journal articles
- Documented institutional datasets (CMHC, NRCan)

### Unacceptable Sources

- Proprietary scraped data
- Unclear third-party compilations
- Unverified crowd-sourced data (without explicit approval)
- Sources without documented licences

---

## 12. Key Technical Context

### Data Schema (all fields TEXT except fid and geom)

```
fid, geom, id, source_id, source, dataset, csduid, csdname,
prov_terr, name, type, address, year_built, units, floors, sq_ft, height
```

### Completeness Summary (from initial inspection)

| Province | Records | Type | Floors | Units | Height |
|----------|---------|------|--------|-------|--------|
| AB | 1,334,404 | 38.5% | 0.2% | 0.0% | 10.6% |
| BC | 1,303,603 | 11.4% | 3.2% | 0.0% | 26.5% |
| MB | 656,775 | 0.0% | 0.0% | 0.0% | 0.0% |
| NB | 661,827 | 17.8% | 0.2% | 8.0% | 3.3% |
| NL | 187,694 | 0.0% | 0.0% | 0.0% | 0.0% |
| NS | 528,307 | 25.0% | 0.8% | 23.0% | 0.0% |
| NT | 11,811 | 94.9% | 0.0% | 0.0% | 0.0% |
| ON (3 files) | 5,695,485 | 5–26% | 3–9% | 0–2% | 4–17% |
| PE | 85,856 | 0.0% | 0.0% | 0.0% | 0.0% |
| QC (2 files) | 3,679,721 | 5–17% | 0.0% | 0.0% | 0.0% |
| SK | 259,461 | 0.1% | 0.0% | 0.0% | 0.0% |
| YT | 12,485 | 0.0% | 0.0% | 0.0% | 0.0% |

### Key Observations for Agents

- Many provinces have **zero** populated attributes beyond geometry and source info
- "Automatically Extracted Buildings" (satellite-derived) have geometry only
- Ontario and BC have the richest attribute data
- Nova Scotia uniquely has 23% unit-count coverage
- National MURB identification **cannot rely solely on ODB attributes** for most provinces

---

## 13. Issue Backlog

The following issues represent the sequenced implementation plan:

1. **Repository scaffold and development environment** (Phase 0) ✅
2. **National GeoPackage inventory** — File hashes, layer inspection, row counts
3. **Source schema audit** — Distinct values for type, source; normalization mapping
4. **Normalized data model** — Common schema, GeoParquet output
5. **Geometry validation** — Validity checks, repair, quality flags
6. **Footprint metric extraction** — Area, dimensions, aspect ratio, compactness
7. **Source-level data-quality dashboard** — Completeness matrix visualization
8. **MURB classification framework** — Rules engine with confidence scores
9. **Manual classification validation sample** — Stratified review protocol
10. **Shape-classification prototype** — Geometric shape family assignment
11. **Processed GeoParquet pipeline** — Partitioned intermediate storage
12. **Descriptive statistics** — Distributions by region, source, class
13. **Excel report generator** — Formatted workbook with standard sheets
14. **Streamlit visualization application** — Interactive exploration tool
15. **Authoritative data-enrichment framework** — External source integration
16. **Height and storey enrichment** — LiDAR/NRCan integration
17. **National representativeness assessment** — Bias analysis and weighting
18. **Archetype methodology** — Clustering approach and validation
19. **Medoid archetype selection** — Representative actual buildings
20. **Synthetic parametric geometry** — Constructed from parameters
21. **Intermediate simulation geometry model** — Format-independent building model
22. **gbXML exporter** — XML generation from intermediate model
23. **gbXML schema validation** — XSD validation and error reporting
24. **OpenStudio import validation** — Actual import testing
25. **Canada-wide production run** — Full national processing
26. **Methodology report** — Complete analytical documentation
27. **Publication-quality figures and tables** — Final outputs

Each issue should include: objective, scope, non-scope, dependencies, deliverables, acceptance criteria, testing expectations, documentation impacts, and known risks.

---

## 14. File and Module Map

| Module | Purpose | Phase |
|--------|---------|-------|
| `src/murb_geometry/cli.py` | Typer CLI commands | 0+ |
| `src/murb_geometry/config.py` | Configuration loading | 0 |
| `src/murb_geometry/logging.py` | Structured logging | 0 |
| `src/murb_geometry/models/` | Pydantic domain models | 0+ |
| `src/murb_geometry/ingestion/` | GeoPackage discovery and reading | 1 |
| `src/murb_geometry/normalization/` | Schema normalization | 2 |
| `src/murb_geometry/validation/` | Geometry validation and repair | 2 |
| `src/murb_geometry/geometry/` | Metric extraction and shape analysis | 2 |
| `src/murb_geometry/classification/` | MURB classification rules | 3 |
| `src/murb_geometry/statistics/` | Descriptive statistics | 4 |
| `src/murb_geometry/visualization/` | Plotly charts and map components | 4 |
| `src/murb_geometry/excel/` | Formatted Excel workbook generation | 4 |
| `src/murb_geometry/reporting/` | Quality reports and manifests | 4 |
| `src/murb_geometry/enrichment/` | External data integration | 5 |
| `src/murb_geometry/archetypes/` | Clustering and representative selection | 6 |
| `src/murb_geometry/gbxml/` | gbXML generation and validation | 7 |
| `app/streamlit_app.py` | Interactive visualization application | 4 |
| `config/` | YAML configuration files | 0+ |
| `tests/` | Test suite | 0+ |

---

## 15. Configuration Reference

All research parameters are in `config/default.yaml`. Key sections:

- `paths` — Directory structure
- `input` — File patterns, CRS, missing-value markers
- `classification` — MURB unit thresholds, confidence levels
- `storey_bands` — Configurable height class boundaries
- `geometry` — Simplification tolerances, orientation bins
- `shape_classification` — Rectangularity, elongation, convexity thresholds
- `outliers` — Detection method and parameters
- `archetypes` — Clustering method, features, random seed
- `wwr` — Default archetypal window-to-wall ratios
- `gbxml` — Schema version, units
- `reproducibility` — Random seed, deterministic flag
- `logging` — Level and format

Override locally by copying `config/local.example.yaml` to `config/local.yaml`.

---

## 16. Quick Reference Commands

```bash
# Development setup
make dev

# Code quality
make lint          # Ruff lint + format check
make format        # Auto-format
make typecheck     # Mypy strict mode
make test          # Pytest
make test-cov      # Pytest with coverage

# CLI (when implemented)
murb-geometry --help
murb-geometry inventory
murb-geometry inspect <file.gpkg>
murb-geometry metrics --province NS
murb-geometry classify --province NS
murb-geometry summarize
murb-geometry excel
murb-geometry visualize
murb-geometry gbxml
murb-geometry run
```
