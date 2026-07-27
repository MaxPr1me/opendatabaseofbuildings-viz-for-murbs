# Software Architecture

## Design Principles

1. **Modular**: Each pipeline stage is an independent module
2. **Configurable**: All thresholds and decisions in YAML configuration
3. **Reproducible**: Deterministic outputs, random seeds, manifests
4. **Memory-efficient**: Province-level processing, no full national load
5. **Typed**: Pydantic models, type annotations, mypy-checked
6. **Testable**: Pure functions, dependency injection, synthetic fixtures
7. **Extensible**: New sources, classifiers, and exporters as plugins

## Module Dependency Graph

```
config → ingestion → normalization → validation
                                        ↓
                               classification → geometry → statistics
                                                    ↓          ↓
                                              enrichment → archetypes
                                                              ↓
                                              visualization ← excel
                                                              ↓
                                                           gbxml
```

## Data Flow

```
GeoPackage (EPSG:3347)
    → Read with pyogrio (column projection, spatial filter)
    → Normalize schema (preserve originals)
    → Validate geometry
    → Classify (confidence-based)
    → Calculate metrics (projected CRS)
    → Store as GeoParquet (partitioned by province/source)
    → Summarize statistics
    → Derive archetypes
    → Generate reports (Excel, HTML, gbXML)
```

## Key Technology Choices

| Concern | Choice | Rationale |
|---------|--------|-----------|
| GeoPackage reading | pyogrio | Fast, column projection, spatial filter |
| Geometry operations | shapely 2.0+ | Vectorized, GEOS-backed |
| Tabular processing | pandas/geopandas | Mature geospatial ecosystem |
| Large queries | duckdb + spatial | SQL analytics, predicate pushdown |
| Intermediate storage | GeoParquet | Columnar, partitioned, fast |
| Configuration | pydantic + YAML | Validated, typed, documented |
| CLI | typer | Modern, type-based, auto-docs |
| Visualization | streamlit + plotly | Interactive, no ArcGIS |
| Excel reports | openpyxl | Full formatting control |
| XML export | lxml | Fast, schema validation |
| Testing | pytest | Industry standard |
| Linting | ruff | Fast, comprehensive |

## Architecture Decision Records

See [docs/adr/](adr/) for documented decisions.
