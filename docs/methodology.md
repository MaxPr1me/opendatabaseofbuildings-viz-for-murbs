# Methodology

## Overview

This document describes the analytical methodology for characterizing representative Canadian MURB geometries from the Statistics Canada Open Database of Buildings (ODB v3).

## Classification Pathway: Option C — Multi-pathway Reporting

The workflow implements Option C from the methodological decision gate. The MURB target is
the **NBC Part 3** class (multi-unit residential of 4+ storeys, or > 600 m² building area);
Part 9 low-rise (duplex, semi-detached, townhouse, single-family) is excluded.

1. **Precision pathway** — Storey/unit-verified MURBs: an explicit
   apartment/multi-residential/condominium type corroborated by floors ≥ 4 or units ≥ 4
   (R001), or floors ≥ 4 (R002) or units ≥ 4 (R003) in a residential/unknown context.
   Confidence levels: `confirmed_murb`, `high_confidence_murb`.

2. **Tiered pathway** — Precision plus probable (height ≥ 12 m as a storey proxy, R004)
   and possible candidates (a MURB-intent type without storey/unit corroboration, R005;
   or a large residential footprint ≥ 600 m², R006).
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

### 2. Type Normalization
- Map observed source `type` values to canonical categories via a **data-derived** mapping
  (`config/type_normalization.yaml`), generated from the full-population schema audit and
  covering English and French/Québec vocabulary — no hand-invented values
- Preserve original values alongside normalized values
- Regenerate the mapping with `scripts/propose_type_normalization.py` after re-auditing

### 3. Geometry Validation
- Verify CRS is projected (EPSG:3347 — NAD83/Statistics Canada Lambert)
- Check geometry validity (OGC rules)
- Repair invalid geometries (store repairs separately)
- Flag empty, null, and degenerate geometries
- Record geometry-quality metrics

### 4. MURB Classification (Multi-pathway, NBC Part 3)
- Explicit non-MURB types (single-family, low-rise multi, non-residential) are excluded first (R010)
- Apply evidence-based rules in priority order (R001–R011 + R999 default): R001 MURB-type +
  storeys/units → confirmed; R002 floors ≥ 4 / R003 units ≥ 4 → high confidence; R004 height ≥ 12 m
  → probable; R005 MURB-type unverified / R006 large residential footprint → possible
- Thresholds are configurable in `config/default.yaml` (storeys, height, footprint, units)
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
- Area, perimeter, compactness, and convexity are vectorized (GeoSeries); MRR axes, holes,
  and vertex counts are computed per geometry

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
