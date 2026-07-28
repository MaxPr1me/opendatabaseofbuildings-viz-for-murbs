# Output Specification

## Overview

This document defines all required outputs from the Canadian MURB Geometry Analysis workflow.
Every output must be producible from the complete eligible population using documented methods.

## Classification Pathway: Option C — Multi-pathway Reporting

Two populations are processed in parallel:

1. **Precision pathway** — Only buildings with direct authoritative multi-unit evidence
   (explicit apartment/multi-residential type OR observed unit count ≥ configured threshold).
2. **Tiered pathway** — Precision population plus probable/possible MURBs identified via
   floors, height, footprint area, residential context, and other validated indicators.

Both pathways are reported. Sensitivity of distributions and archetypes to pathway
choice is quantified explicitly.

## Research-Question → Output Matrix

| RQ | Question | Required Fields | Method | Output Tables | Output Figures | Pathway |
|----|----------|-----------------|--------|---------------|----------------|---------|
| RQ1 | MURB identification | type, units, floors, height, area | Multi-pathway classification | classification_summary.csv | classification_sankey.html | Both |
| RQ2 | Typical MURB size | footprint_area, floor_area, GFA, length, width, storeys, height, units | Descriptive stats by pathway | size_distributions.csv | size_violin_plots.html | Both |
| RQ3 | Building form | aspect_ratio, orientation, compactness, rectangularity, convexity, facades | Geometry metrics | form_metrics.csv | form_scatter.html | Both |
| RQ4 | Shape classification | shape_class, rectangularity, convexity, holes | Rule-based + metrics | shape_classes.csv | shape_examples.html | Both |
| RQ5 | Mid-rise/High-rise | storeys, height, code thresholds | Storey-band analysis | storey_bands.csv | storey_histogram.html | Both |
| RQ6 | WWR | external sources, literature | Documented assumptions | wwr_assumptions.csv | wwr_by_facade.html | Both |
| RQ7 | Representative archetypes | all geometry + classification | Clustering + medoid | archetypes.json | archetype_scatter.html | Both |
| RQ8 | Geographic variation | province, CSD, climate zone | Stratified statistics | geographic_variation.csv | province_comparison.html | Both |
| RQ9 | Data quality | all fields, source, completeness | Completeness analysis | data_quality_matrix.csv | completeness_heatmap.html | N/A |
| RQ10 | Simulation suitability | gbXML validation, import tests | Schema + import validation | validation_results.csv | N/A | Both |

## Required Output Families

### 1. Data Quality & Audit
- `outputs/reports/inventory.json` — GeoPackage inventory with hashes
- `outputs/reports/schema_audit.csv` — Field types, parsing rates, distinct values
- `outputs/reports/source_completeness.csv` — Completeness by source organization
- `outputs/reports/data_quality_matrix.csv` — Province × field completeness
- `outputs/reports/exclusion_report.csv` — Records excluded and reasons
- `outputs/reports/run_manifest.json` — Timings, counts, hashes, config, versions

### 2. Classification
- `outputs/reports/classification_summary.csv` — Counts by pathway, confidence, province
- `outputs/reports/classification_evidence.parquet` — Building-level evidence chains
- `outputs/reports/pathway_sensitivity.csv` — Comparison of precision vs tiered results

### 3. Geometry & Metrics
- `data/processed/murbs_precision.parquet` — Full-population precision-pathway GeoParquet
- `data/processed/murbs_tiered.parquet` — Full-population tiered-pathway GeoParquet
- `outputs/reports/geometry_metrics_summary.csv` — Descriptive stats by pathway/province

### 4. Statistics & Distributions
- `outputs/reports/size_distributions.csv` — Percentiles for all size metrics
- `outputs/reports/form_metrics.csv` — Shape/form distributions
- `outputs/reports/storey_bands.csv` — Mid-rise/high-rise breakdown
- `outputs/reports/geographic_variation.csv` — Province-level comparisons

### 5. Archetypes
- `outputs/archetypes/precision_archetypes.json` — Precision-pathway archetypes
- `outputs/archetypes/tiered_archetypes.json` — Tiered-pathway archetypes
- `outputs/archetypes/cluster_diagnostics.json` — Silhouette, inertia, stability
- `outputs/archetypes/medoid_geometries/` — Actual medoid footprints (GeoJSON)

### 6. Simulation Geometry
- `outputs/gbxml/` — gbXML exports per archetype
- `outputs/gbxml/validation/` — XSD and structural validation reports

### 7. Reports & Figures
- `outputs/reports/research_report.md` — Direct answers to RQ1–RQ10
- `outputs/figures/` — All publication-quality figures (HTML interactive + PNG static)
- `outputs/excel/murb_analysis.xlsx` — Formatted workbook

### 8. Streamlit Application
- `app/streamlit_app.py` — Interactive exploration using persisted analytical outputs

## Claim Requirements

Every quantitative claim in outputs must include:
- Population definition (pathway, confidence classes, geography)
- Source dataset and version (ODB v3)
- Record count (before and after exclusions)
- Observed/estimated/assumed status
- Missingness percentage
- Uncertainty description

## Validation Requirements

- All statistics computed from complete eligible population (no arbitrary caps)
- Reproducible with same config + data = same outputs (seed: 42)
- gbXML validates against XSD 7.03
- Run manifest records all stage outcomes
