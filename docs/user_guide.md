# User Guide

## Status: Planned

This guide will be expanded as features are implemented.

## Installation

### Prerequisites
- Python 3.12 or later
- [uv](https://docs.astral.sh/uv/) package manager (recommended)

### Setup

```bash
# Clone the repository
git clone https://github.com/MaxPr1me/opendatabaseofbuildings-viz-for-murbs.git
cd opendatabaseofbuildings-viz-for-murbs

# Install with uv
uv pip install -e ".[dev]"
```

### Data Setup

1. Download ODB v3 GeoPackage files from Statistics Canada
2. Place each provincial file in `data/ODB_v3_XX/ODB_v3_XX.gpkg`
3. Verify with `murb-geometry inventory`

## Quick Start

```bash
# Inspect a data file
murb-geometry inspect data/ODB_v3_NS/ODB_v3_NS.gpkg

# Run data inventory
murb-geometry inventory

# Launch visualization
murb-geometry visualize

# Generate Excel report
murb-geometry excel --output outputs/excel/murb_report.xlsx
```

## Configuration

- Default settings: `config/default.yaml`
- Local overrides: copy `config/local.example.yaml` to `config/local.yaml`
- Classification rules: `config/classification_rules.yaml`
- Archetype parameters: `config/archetypes.yaml`
