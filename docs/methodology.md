# Methodology

## Overview

This document describes the analytical methodology for characterizing representative Canadian MURB geometries from the Statistics Canada Open Database of Buildings.

## Pipeline Stages

### 1. Data Ingestion
- Discover GeoPackage files under `data/`
- Inspect layers, CRS, schemas, and row counts
- Record file hashes and provenance
- Parse text fields to numeric where applicable
- Normalize missing-value markers (`..`) to null

### 2. Schema Normalization
- Map source-specific field values to a common taxonomy
- Preserve original values alongside normalized values
- Document all normalization rules

### 3. Geometry Validation
- Verify CRS is projected (EPSG:3347)
- Check geometry validity (OGC rules)
- Repair invalid geometries (store repairs separately)
- Flag empty, null, and degenerate geometries
- Record geometry-quality metrics

### 4. MURB Classification
- Apply evidence-based rules (see `config/classification_rules.yaml`)
- Assign confidence levels
- Preserve all evidence and rule references
- Support manual validation sampling

### 5. Geometry Metric Extraction
- Calculate footprint area, perimeter, dimensions
- Compute minimum rotated rectangle
- Derive aspect ratio, compactness, rectangularity, convexity
- Extract facade segments and orientations
- Count holes and components

### 6. Shape Classification
- Assign footprints to shape families
- Use geometric metrics and topology
- Support both robust and experimental classifiers
- Record confidence and method

### 7. Descriptive Statistics
- Compute distributions by province, source, storey band, shape class
- Report completeness, missingness, outliers
- Provide percentile ranges

### 8. Enrichment (Future)
- Integrate authoritative external data
- Height from LiDAR
- Unit counts from CMHC
- Age from assessment records

### 9. Archetype Derivation
- Cluster buildings by geometry similarity
- Select medoid representatives
- Construct synthetic parametric forms
- Document uncertainty ranges

### 10. Simulation Export (Future)
- Generate intermediate building geometry model
- Export to gbXML
- Validate against schema
- Test import into OpenStudio

## Key Methodological Constraints

- Footprint ≠ typical floor plate (podiums, setbacks, additions)
- Footprints do not provide WWR
- National aggregation requires weighting or stratification
- Source coverage is non-random
- All thresholds are configurable
