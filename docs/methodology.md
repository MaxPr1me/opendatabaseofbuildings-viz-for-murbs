# Methodology

## Overview

This document describes the analytical methodology for characterizing representative Canadian MURB geometries from the Statistics Canada Open Database of Buildings (ODB v3).

## Classification Pathway: Option C — Multi-pathway Reporting

The workflow implements Option C from the methodological decision gate:

1. **Precision pathway** — Only buildings with direct authoritative multi-unit evidence
   (explicit apartment/multi-residential type OR observed unit count ≥ 4).
   Confidence levels: `confirmed_murb`, `high_confidence_murb`.

2. **Tiered pathway** — Precision population plus probable/possible MURBs identified via
   floors ≥ 4 + area ≥ 400 m², large residential footprints, or tall buildings.
   Confidence levels: `confirmed_murb`, `high_confidence_murb`, `probable_murb`, `possible_murb`.

Both pathways are processed in parallel. Sensitivity of geometry distributions and
archetypes to classification pathway choice is quantified explicitly.

## Pipeline Stages

### 1. Data Ingestion (Full Population)
- Discover all 15 GeoPackage files across 12 provinces/territories
- Load **complete populations** — no arbitrary row caps
- Merge split files (Ontario: 3 files → 1, Quebec: 2 files → 1)
- Record file hashes, row counts, and provenance
- Parse text fields to numeric where applicable
- Normalize missing-value markers (`..`, empty, `NA`, `N/A`) to null

### 2. Schema Normalization
- Map 40+ source-specific type values to canonical categories
- Preserve original values alongside normalized values
- Document all normalization rules in `classification/classifier.py`

### 3. Geometry Validation
- Verify CRS is projected (EPSG:3347 — NAD83/Statistics Canada Lambert)
- Check geometry validity (OGC rules)
- Repair invalid geometries (store repairs separately)
- Flag empty, null, and degenerate geometries
- Record geometry-quality metrics

### 4. MURB Classification (Multi-pathway)
- Apply 11 evidence-based rules (R001–R011 + R999 default)
- Assign confidence levels with scores (1.0 → 0.0)
- Preserve all evidence fields, rule IDs, and reasoning text
- Filter into precision and tiered populations
- **No arbitrary row limits** — all records classified

### 5. Geometry Metric Extraction
- Calculate footprint area, perimeter, dimensions
- Compute minimum rotated rectangle (MRR)
- Derive aspect ratio, compactness (Polsby-Popper), rectangularity, convexity
- Extract hole/courtyard metrics, component/vertex counts
- Compute orientation (azimuth of major axis)
- Vectorized where possible, row-by-row for complex metrics

### 6. Shape Classification
- Assign footprints to shape families based on metrics
- Use rectangularity (≥0.90), elongation (≥3.0), convexity (≥0.85) thresholds
- Detect courtyard (hole fraction ≥0.05)
- Record confidence and method

### 7. Descriptive Statistics
- Compute distributions by province, source, storey band, shape class
- Report completeness, missingness, outliers
- Provide percentile ranges (P5, P10, P25, P50, P75, P90, P95)
- Stratify by classification pathway

### 8. Enrichment (Future)
- Integrate authoritative external data
- Height from LiDAR
- Unit counts from CMHC
- Age from assessment records

### 9. Archetype Derivation (Evidence-based)
- Evaluate multiple k values with diagnostics (silhouette, inertia, stability)
- Select cluster count based on empirical evidence, not convenience
- Cluster buildings by geometry features (area, aspect ratio, compactness)
- Select medoid representatives (actual buildings)
- Construct synthetic parametric forms for shape families
- Document uncertainty ranges per archetype
- Run independently per pathway to quantify sensitivity

### 10. Simulation Export
- Generate intermediate BuildingGeometryModel
- Support multiple geometry pathways (medoid extrusion, simplified, synthetic)
- Export to gbXML 7.03
- Validate against XSD
- WWR from external sources/assumptions only (never from ODB footprints)

### 11. Research Report
- Answer RQ1–RQ10 directly with evidence
- Provide min/central/max simulation ranges
- Stratify by pathway, geography, confidence class

## Key Methodological Constraints

- **Full-population rule**: All production statistics from complete eligible population
- Footprint ≠ typical floor plate (podiums, setbacks, additions)
- Footprints cannot provide WWR — must use external sources
- National aggregation requires awareness of uneven source coverage
- All thresholds are configurable via `config/default.yaml`
- Classification semantics must be consistent nationally
- Sampling allowed only for tests, previews, and explicitly-labelled exploratory analysis
