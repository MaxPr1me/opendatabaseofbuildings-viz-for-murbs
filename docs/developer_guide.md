# Developer Guide

## Status: Planned

## Project Structure

```
src/murb_geometry/      ← Main package
├── cli.py              ← Typer CLI commands
├── config.py           ← Configuration loading
├── logging.py          ← Structured logging
├── models/             ← Pydantic data models
├── ingestion/          ← GeoPackage reading
├── validation/         ← Geometry validation
├── normalization/      ← Schema normalization
├── classification/     ← MURB classification
├── geometry/           ← Metric extraction
├── enrichment/         ← External data integration
├── statistics/         ← Summary statistics
├── archetypes/         ← Representative geometry
├── visualization/      ← Charts and maps
├── reporting/          ← Quality reports
├── excel/              ← Workbook generation
└── gbxml/              ← Simulation export
```

## Development Workflow

```bash
# Install dev dependencies
make dev

# Run linting
make lint

# Run type checking
make typecheck

# Run tests
make test

# Format code
make format
```

## Adding a New Module

1. Create `src/murb_geometry/your_module/__init__.py`
2. Add typed public interface
3. Create tests in `tests/unit/test_your_module.py`
4. Update documentation
5. Add CLI command if user-facing

## Governance and Methodological Safeguards

All analytical work is governed by:

- [`AGENTS.md`](../AGENTS.md) — Controlling instruction document for coding agents
- [`docs/AGENTIC_REBUILD_PROMPT.md`](AGENTIC_REBUILD_PROMPT.md) — Detailed methodological
  safeguards and rebuild rationale
- [Agentic rebuild epic (issue #1)](https://github.com/MaxPr1me/opendatabaseofbuildings-viz-for-murbs/issues/1) — Master tracking issue

Key rules: no arbitrary row caps on research outputs, decision gates for material assumptions,
push-and-update protocol after every major task. See `AGENTS.md` §16 for the full list.

## Key Conventions

- Type-annotate all public functions
- Use pydantic models for structured data
- Load configuration via `murb_geometry.config.load_config()`
- Use `murb_geometry.logging.setup_logging()` for output
- Pure functions where practical
- Vectorized geospatial operations with geopandas/shapely
- Province-level processing for memory efficiency
