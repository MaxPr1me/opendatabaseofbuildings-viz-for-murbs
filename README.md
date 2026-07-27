# Canadian MURB Geometry Analysis

**Characterizing representative multi-unit residential building geometries across Canada using the Statistics Canada Open Database of Buildings**

[![Status: National Run Complete](https://img.shields.io/badge/status-National%20Run%20Complete-brightgreen)]()
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)]()
[![License: MIT](https://img.shields.io/badge/license-MIT-green)]()
[![Tests: 99 passing](https://img.shields.io/badge/tests-99%20passing-brightgreen)]()

---

## Project Summary

This repository implements a reproducible national analytical workflow to identify, characterize, summarize, visualize, and eventually export representative Canadian **MURB** (Multi-Unit Residential Building) geometries for building-performance simulation.

### Why representative MURB geometry matters

Energy-performance modelling with [OpenStudio](https://openstudio.net/) and [EnergyPlus](https://energyplus.net/) requires defensible building geometry inputs. Researchers and practitioners need representative building forms—floor-plate areas, aspect ratios, storeys, orientations, facade dimensions—grounded in the actual Canadian building stock rather than arbitrary assumptions.

### Why the Statistics Canada Open Database of Buildings

The [Open Database of Buildings (ODB)](https://www.statcan.gc.ca/en/lode/databases/odb) provides the most comprehensive national compilation of building footprints in Canada, aggregating municipal, provincial, and federal open-data sources. It contains approximately **14.4 million building footprint records** across all provinces and territories.

### Why the source is insufficient alone

The ODB is a heterogeneous compilation—not a homogeneous building registry. Key limitations include:
- Building-type classifications are sparse and source-specific (0–95% populated)
- Storey counts are available for only 0–9% of records
- Height data exists for only 0–27% of records
- Dwelling-unit counts are available for only 0–23% of records
- Footprints alone cannot provide window-to-wall ratios
- National coverage is non-random (depends on municipal open-data policies)

This project addresses these limitations through transparent classification, data-quality assessment, external enrichment, and careful statistical methodology.

---

## Research Questions

### Building population and classification
- How can MURBs be reliably identified from heterogeneous footprint data?
- What confidence can be assigned to each classification?

### Typical MURB size
- What are defensible distributions for footprint area, floor-plate area, gross floor area, building dimensions, storeys, height, unit count, and units per floor?

### Building form and aspect ratio
- What are the characteristic aspect ratios, orientations, compactness values, and facade dimensions of Canadian MURBs?

### Shape classification
- Can footprints be classified into simulation-oriented shape families (rectangle, slab, L, T, U, H, courtyard, tower, podium-and-tower)?

### Mid-rise and high-rise definitions
- What storey/height boundaries meaningfully distinguish building classes for simulation, considering code requirements, construction systems, and energy performance?

### Window-to-wall ratio
- How should WWR be handled when footprints provide only facade orientation and length?
- What archetypal or external-data-driven assumptions are defensible?

### Representative archetypes
- How can representative simulation geometries be derived from the building population using clustering, medoids, and parametric synthesis?

### Geographic variation
- How do MURB characteristics vary by province, climate zone, urban context, and construction era?

### Data quality and representativeness
- Is the sample representative of the national MURB stock?
- What biases exist and how should they be reported?

---

## Scope

### Current scope (Phase 0)
- Repository structure and documentation
- Software architecture and configuration schema
- Phased implementation roadmap
- Development environment

### Future scope (Phases 1–8)
- National data inventory and quality audit
- Geometry metric extraction
- MURB classification with confidence scores
- Interactive visualization (Streamlit)
- Formatted Excel reports
- External data enrichment
- Representative archetype derivation
- gbXML export for OpenStudio/EnergyPlus

### Non-goals
- Real-time web application deployment
- Individual building energy simulation
- Proprietary GIS integration (ArcGIS/QGIS as runtime requirement)
- Privacy-sensitive operations on individual buildings
- Complete urban building energy modelling

### Unsupported conclusions
This repository does **not** and **will not**:
- Claim that footprint area equals typical floor-plate area
- Calculate actual WWR from footprints alone
- Present unweighted national statistics as representative without caveats
- Average polygon coordinates from unrelated buildings
- Claim OpenStudio compatibility without import validation

---

## Data

### Expected data directory

```
data/
├── ODB_v3_AB/ODB_v3_AB.gpkg       (Alberta — 1.3M records, 572 MB)
├── ODB_v3_BC/ODB_v3_BC.gpkg       (British Columbia — 1.3M records, 618 MB)
├── ODB_v3_MB/ODB_v3_MB.gpkg       (Manitoba — 657K records, 299 MB)
├── ODB_v3_NB/ODB_v3_NB.gpkg       (New Brunswick — 662K records, 257 MB)
├── ODB_v3_NL/ODB_v3_NL.gpkg       (Newfoundland & Labrador — 188K records, 75 MB)
├── ODB_v3_NS/ODB_v3_NS.gpkg       (Nova Scotia — 528K records, 227 MB)
├── ODB_v3_NT/ODB_v3_NT.gpkg       (Northwest Territories — 12K records, 5 MB)
├── ODB_v3_ON_1/ODB_v3_ON_1.gpkg   (Ontario 1/3 — 2.0M records, 890 MB)
├── ODB_v3_ON_2/ODB_v3_ON_2.gpkg   (Ontario 2/3 — 2.0M records, 920 MB)
├── ODB_v3_ON_3/ODB_v3_ON_3.gpkg   (Ontario 3/3 — 1.7M records, 713 MB)
├── ODB_v3_PE/ODB_v3_PE.gpkg       (Prince Edward Island — 86K records, 35 MB)
├── ODB_v3_QC_1/ODB_v3_QC_1.gpkg   (Quebec 1/2 — 2.0M records, 862 MB)
├── ODB_v3_QC_2/ODB_v3_QC_2.gpkg   (Quebec 2/2 — 1.7M records, 747 MB)
├── ODB_v3_SK/ODB_v3_SK.gpkg       (Saskatchewan — 259K records, 116 MB)
└── ODB_v3_YT/ODB_v3_YT.gpkg       (Yukon — 12K records, 5 MB)
```

**Total: ~14.4 million records, ~6.3 GB**

### Supported file types
- GeoPackage (`.gpkg`) — primary input format
- GeoParquet (`.parquet`) — intermediate analytical format

### GeoPackage layer discovery
Each `.gpkg` file contains a single layer named identically to the file (e.g., `ODB_v3_NS` in `ODB_v3_NS.gpkg`).

### Raw-data handling
- Raw GeoPackage files are **never modified** by the pipeline
- Processed outputs are stored separately in `data/interim/` and `data/processed/`
- Original field values are preserved alongside normalized fields

### Licensing
Statistics Canada Open Database of Buildings is released under the [Open Government Licence — Canada](https://open.canada.ca/en/open-government-licence-canada). Individual source datasets have additional attribution requirements documented in `ODB_v3_data_providers.csv`.

### Data not committed to Git
GeoPackage files (6+ GB) are excluded via `.gitignore`. Only metadata files (`data/README.md`, `ODB_v3_data_providers.csv`) are tracked.

### CRS
All GeoPackage files use **EPSG:3347** (NAD83 / Statistics Canada Lambert) — a projected CRS suitable for area and distance calculations across Canada.

---

## Quick Start

### Prerequisites
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended package manager)

### Installation

```bash
git clone https://github.com/MaxPr1me/opendatabaseofbuildings-viz-for-murbs.git
cd opendatabaseofbuildings-viz-for-murbs

# Install with uv (recommended)
uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"

# Set up pre-commit hooks
pre-commit install
```

### Commands (planned)

```bash
# Inspect a data file
murb-geometry inspect data/ODB_v3_NS/ODB_v3_NS.gpkg

# Run data inventory
murb-geometry inventory

# Calculate geometry metrics
murb-geometry metrics --province NS

# Classify candidate MURBs
murb-geometry classify --province NS

# Generate summary statistics
murb-geometry summarize --province NS

# Produce Excel report
murb-geometry excel --output outputs/excel/murb_report.xlsx

# Generate representative archetypes
murb-geometry archetypes --method medoid

# Launch visualization tool
murb-geometry visualize
# (equivalent to: streamlit run app/streamlit_app.py)

# Export gbXML (future)
murb-geometry gbxml --archetype-id A001 --output outputs/gbxml/archetype_A001.xml

# Run complete pipeline
murb-geometry run --config config/default.yaml

# Run tests
make test

# Run linting
make lint

# Run type checking
make typecheck
```

---

## Outputs

| Output | Format | Description |
|--------|--------|-------------|
| Processed buildings | GeoParquet | Partitioned by province/source with metrics |
| Summary statistics | CSV | Distributions by province, source, class |
| Excel workbooks | .xlsx | Formatted reports with multiple sheets |
| Interactive visualization | Streamlit HTML | Maps, charts, filters |
| Static figures | PNG/SVG | Publication-quality charts |
| Data-quality reports | HTML/CSV | Completeness and quality matrices |
| Archetype definitions | YAML/JSON | Representative geometry parameters |
| gbXML files | .xml | Simulation geometry (future) |
| Run manifests | JSON | Reproducibility records |

---

## Methodology Overview

1. **Ingestion** — Discover and read GeoPackage files with pyogrio (column projection, spatial filtering)
2. **Schema normalization** — Map source-specific values to common taxonomy, preserving originals
3. **Geometry validation** — Check/repair geometry, flag quality issues
4. **MURB classification** — Apply evidence-based rules with confidence scores
5. **Metric extraction** — Calculate area, dimensions, aspect ratio, compactness, shape
6. **Data-quality assessment** — Report completeness by province, source, field
7. **Enrichment** — Integrate external authoritative data (height, units, age)
8. **Weighting and stratification** — Address non-random coverage
9. **Clustering** — Group buildings by geometric similarity
10. **Archetype selection** — Medoid, quantile, or synthetic representative
11. **Validation** — Manual review, cross-source checks, simulation testing
12. **Export** — gbXML, Excel, GeoParquet, figures

See [docs/methodology.md](docs/methodology.md) for complete details.

---

## Limitations

> **Critical constraints that all users must understand:**

1. **Footprints ≠ floor plates** — Ground-level footprints may include podiums, garages, and additions that differ from typical upper floors
2. **No WWR from footprints** — Window-to-wall ratio requires external data or archetypal assumptions
3. **Storeys and height are incomplete** — Available for <10% and <27% of records respectively
4. **Source coverage is uneven** — Results depend on which municipalities publish open data
5. **National results require weighting** — Unweighted aggregation would overrepresent data-rich cities
6. **MURB identification may require external evidence** — Many provinces have 0% building-type data

---

## Development Status

| Component | Status |
|-----------|--------|
| Repository scaffold | ✅ Complete |
| Configuration schema | ✅ Complete |
| Documentation | ✅ Complete |
| Data inventory — 14.4M records (Phase 1) | ✅ Complete |
| Geometry metrics (Phase 2) | ✅ Complete |
| Geometry validation (Phase 2) | ✅ Complete |
| MURB classification (Phase 3) | ✅ Complete |
| Descriptive statistics (Phase 4) | ✅ Complete |
| Excel reports (Phase 4) | ✅ Complete |
| Streamlit visualization (Phase 4) | ✅ Complete |
| Enrichment framework (Phase 5) | ✅ Framework |
| K-means clustering + medoids (Phase 6) | ✅ Complete |
| gbXML exporter (Phase 7) | ✅ Complete |
| National production run (Phase 8) | ✅ Complete |
| NS MURB characterization (2,766 buildings) | ✅ Complete |
| 6 representative archetypes | ✅ Complete |
| External source connectors (Phase 5) | 📋 Future |
| XSD validation + OpenStudio import | 📋 Future |

---

## Reproducibility

- **Configuration files** — All research decisions in versioned YAML (`config/`)
- **Random seeds** — Fixed seeds for clustering and sampling (default: 42)
- **Environment locking** — Dependencies pinned via `uv.lock`
- **Data hashes** — File checksums recorded in processing manifests
- **Run manifests** — Every execution records inputs, config, versions, outputs
- **Versioned rules** — Classification and normalization rules carry version numbers
- **Deterministic outputs** — Same inputs + config = same outputs

---

## Technology Stack

| Purpose | Library |
|---------|---------|
| GeoPackage I/O | pyogrio |
| Geospatial operations | geopandas, shapely |
| CRS management | pyproj |
| Tabular data | pandas |
| Analytical queries | duckdb (spatial extension) |
| Intermediate storage | GeoParquet |
| Numerical computing | numpy, scipy |
| Clustering | scikit-learn |
| Configuration | pydantic, PyYAML |
| CLI | typer |
| Visualization | streamlit, plotly, pydeck |
| Excel reports | openpyxl |
| XML/gbXML | lxml |
| Testing | pytest |
| Linting & formatting | ruff |
| Type checking | mypy |
| Git hooks | pre-commit |

---

## Repository Structure

```
opendatabaseofbuildings-viz-for-murbs/
├── README.md                  ← This file
├── AGENTS.md                  ← Coding agent instructions
├── AGENT.md                   ← Redirects to AGENTS.md
├── LICENSE                    ← MIT
├── CITATION.cff               ← Citation metadata
├── CONTRIBUTING.md            ← Contribution guidelines
├── CHANGELOG.md               ← Version history
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── .gitignore
├── .gitattributes
├── .editorconfig
├── .pre-commit-config.yaml
├── pyproject.toml             ← Python project configuration
├── Makefile                   ← Development commands
├── data/                      ← GeoPackage files (not committed)
│   └── README.md              ← Data documentation and inventory
├── config/                    ← YAML configuration
│   ├── default.yaml
│   ├── local.example.yaml
│   ├── data_sources.yaml
│   ├── classification_rules.yaml
│   └── archetypes.yaml
├── docs/                      ← Project documentation
│   ├── index.md
│   ├── research_questions.md
│   ├── methodology.md
│   ├── data_dictionary.md
│   ├── data_quality.md
│   ├── provenance.md
│   ├── architecture.md
│   ├── gbxml_design.md
│   ├── validation_plan.md
│   ├── limitations.md
│   ├── roadmap.md
│   ├── user_guide.md
│   ├── developer_guide.md
│   └── adr/
├── notebooks/                 ← Exploratory Jupyter notebooks
├── src/murb_geometry/         ← Main Python package
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   ├── logging.py
│   ├── models/
│   ├── ingestion/
│   ├── validation/
│   ├── normalization/
│   ├── classification/
│   ├── geometry/
│   ├── enrichment/
│   ├── statistics/
│   ├── archetypes/
│   ├── visualization/
│   ├── reporting/
│   ├── excel/
│   └── gbxml/
├── app/                       ← Streamlit application
│   └── streamlit_app.py
├── tests/                     ← Test suite
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   ├── regression/
│   └── fixtures/
├── scripts/                   ← Utility scripts
├── outputs/                   ← Generated outputs (not committed)
│   ├── README.md
│   ├── reports/
│   ├── excel/
│   ├── figures/
│   ├── maps/
│   ├── archetypes/
│   └── gbxml/
└── .github/
    ├── workflows/ci.yaml
    ├── ISSUE_TEMPLATE/
    └── pull_request_template.md
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

[MIT License](LICENSE)

## Citation

See [CITATION.cff](CITATION.cff) for citation information.

## Acknowledgements

- [Statistics Canada Open Database of Buildings](https://www.statcan.gc.ca/en/lode/databases/odb)
- All source organizations listed in `ODB_v3_data_providers.csv`
- Released under the [Open Government Licence — Canada](https://open.canada.ca/en/open-government-licence-canada)
