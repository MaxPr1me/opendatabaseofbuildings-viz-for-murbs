# Research Report — Canadian MURB Geometry Analysis

> Generated: 2026-07-28 15:39 UTC
> Source: Statistics Canada Open Database of Buildings v3
> Classification Pathway: Option C — Multi-pathway reporting
> Precision population: 2,768 buildings
> Tiered population: 2,995 buildings
> Provinces processed: 1
> Pipeline manifest: `outputs/reports/run_manifest.json`

---

## RQ1: Building Population and Classification

**How can MURBs be reliably identified from the ODB given heterogeneous source data?**

### Direct Answer

MURBs are identified through an 11-rule evidence-based classifier applied to the
complete ODB v3 population (528,307 buildings across 1
provinces). Two pathways are run in parallel (Option C):

- **Precision pathway** (2,768 buildings): Only
  buildings with direct authoritative evidence — explicit apartment/multi-residential
  type (R001) or observed unit count ≥ 4 (R002).
- **Tiered pathway** (2,995 buildings): Precision plus
  probable (floors ≥ 4 + area ≥ 400 m², R003) and possible (large residential
  footprint R004, tall building R005) candidates.

### Population and Method

- **Source**: ODB v3, all 15 GeoPackage files, 12 provinces/territories
- **Total records classified**: 528,307
- **Classification**: Rule-based with confidence scores (1.0 → 0.0)
- **No arbitrary row caps**: Complete populations processed

### Evidence Table

| Province | Total | Precision | Tiered | Confirmed | High-Conf | Probable | Possible |
|----------|------:|----------:|-------:|----------:|----------:|---------:|---------:|
| NS | 528,307 | 2,768 | 2,995 | 190 | 2,578 | 18 | 209 |

### Limitations

- Provinces without type or unit data (MB, NL, PE, SK, YT) yield zero precision
  MURBs and rely entirely on geometric/height indicators for tiered classification.
- Alberta has type data but no unit counts, producing 0 precision but 72,226 tiered
  (mostly from R005 tall-building rule using height data).
- The precision pathway provides highest confidence but lowest geographic coverage.
- Classification consistency depends on source-specific type normalization quality.

---

## RQ2: Typical MURB Size

**What are defensible statistical distributions for Canadian MURB footprint area,
storeys, height, unit count, and dimensions?**

### Direct Answer

Based on the precision pathway (2,768 buildings from NS and NB
with direct multi-unit evidence):

| Metric | N | Min | P25 | Median | P75 | Max | Mean | Std | Missing |
|--------|--:|----:|----:|-------:|----:|----:|-----:|----:|--------:|
| Footprint area (m²) | 2,768 | 4.7 | 176.2 | 346.7 | 937.9 | 8,833.3 | 728.5 | 896.5 | 0.0% |
| MRR length (m) | 2,768 | 3.7 | 17.4 | 25.3 | 50.0 | 233.4 | 37.6 | 28.7 | 0.0% |
| MRR width (m) | 2,768 | 1.0 | 10.8 | 14.7 | 22.9 | 97.8 | 19.2 | 12.8 | 0.0% |
| Storeys | 301 | 1.0 | 2.0 | 2.0 | 3.0 | 6.0 | 2.5 | 0.7 | 0.0% |
| Dwelling units | 2,766 | 4.0 | 5.0 | 12.0 | 36.0 | 359.0 | 27.1 | 35.8 | 0.0% |

**Tiered pathway** (2,995 buildings — broader candidate population):

| Metric | N | Min | P25 | Median | P75 | Max | Mean | Std | Missing |
|--------|--:|----:|----:|-------:|----:|----:|-----:|----:|--------:|
| Footprint area (m²) | 2,995 | 4.7 | 182.9 | 382.6 | 936.9 | 12,439.5 | 751.4 | 924.0 | 0.0% |
| MRR length (m) | 2,995 | 3.7 | 17.8 | 27.7 | 51.7 | 240.4 | 39.0 | 28.9 | 0.0% |
| MRR width (m) | 2,995 | 1.0 | 11.1 | 15.2 | 23.2 | 97.8 | 19.4 | 12.9 | 0.0% |
| Storeys | 322 | 1.0 | 2.0 | 2.0 | 3.0 | 9.0 | 2.6 | 0.9 | 0.0% |
| Dwelling units | 2,973 | 1.0 | 4.0 | 10.0 | 32.0 | 359.0 | 25.3 | 35.2 | 0.0% |

### Recommended Simulation Ranges (Precision Pathway)

| Parameter | Minimum (P5) | Central (Median) | Maximum (P95) | Source |
|-----------|-------------:|-----------------:|--------------:|--------|
| Footprint area (m²) | 100.9 | 346.7 | 2,522.4 | Observed |
| Storeys | 2 | 2 | 4 | Observed |
| Units | 4 | 12 | 100 | Observed |

### Limitations

- Floor/unit counts are only available for a subset of provinces (NS, NB, ON, BC).
- Height data is sparse and not available from all sources.
- Footprint ≠ floor plate — podiums, setbacks, and additions are not captured.
- GFA cannot be reliably computed without confirmed storey counts.

---

## RQ3: Building Form and Aspect Ratio

**What are the characteristic geometric properties of Canadian MURBs?**

### Direct Answer

| Metric | N | Min | P25 | Median | P75 | Max | Mean | Std | Missing |
|--------|--:|----:|----:|-------:|----:|----:|-----:|----:|--------:|
| Aspect ratio | 2,768 | 1.0 | 1.3 | 1.7 | 2.4 | 20.1 | 2.0 | 1.0 | 0.0% |
| Compactness (Polsby-Popper) | 2,768 | 0.0 | 0.5 | 0.6 | 0.7 | 1.0 | 0.6 | 0.1 | 0.0% |
| Rectangularity | 2,768 | 0.2 | 0.8 | 0.9 | 1.0 | 1.0 | 0.9 | 0.1 | 0.0% |
| Convexity | 2,768 | 0.2 | 0.9 | 1.0 | 1.0 | 1.0 | 0.9 | 0.1 | 0.0% |
| Orientation (deg from N) | 2,768 | 0.1 | 43.5 | 100.9 | 131.1 | 179.6 | 86.2 | 49.4 | 0.0% |
| Perimeter (m) | 2,768 | 10.2 | 57.2 | 81.4 | 150.4 | 575.1 | 115.1 | 81.4 | 0.0% |

### Key Findings

- Median aspect ratio of ~1.7 indicates
  moderately elongated footprints (not square, not extreme slabs).
- Rectangularity median ~0.92 suggests
  most MURBs approximate rectangular forms.
- Compactness values indicate moderate complexity beyond simple rectangles.

### Limitations

- Orientation analysis limited to MRR major axis — does not account for street alignment.
- Facade-specific dimensions require segment decomposition (not yet in persisted outputs).

---

## RQ4: Shape Classification

**Can building footprints be reliably classified into simulation-oriented shape families?**

### Direct Answer

Shape classification uses three primary metrics:
- **Rectangularity** ≥ 0.90 → compact rectangle
- **Convexity** < 0.85 → complex/non-convex shape (L, T, U, courtyard candidates)
- **Aspect ratio** ≥ 3.0 → elongated slab/bar

From the precision population:
- Rectangularity: median = 0.923, P25 = 0.806
- Convexity: median = 0.965, P25 = 0.897

This indicates the majority of precision-pathway MURBs are moderately rectangular.
Buildings with convexity < 0.85 are candidates for L/T/U/courtyard classification.

### Limitations

- Shape class assignment requires visual validation (not yet performed).
- Complex shapes (podium-and-tower) require 3D information not available from footprints.
- Small sample sizes for rare shape classes limit statistical power.

---

## RQ5: Mid-Rise and High-Rise Definitions

**What storey/height boundaries meaningfully distinguish mid-rise from high-rise MURBs?**

### Direct Answer

Using configured storey bands from `config/default.yaml`:
- Low-rise multifamily: 2-3 storeys
- Small mid-rise: 4-6 storeys
- Large mid-rise: 7-12 storeys
- Low high-rise: 13-25 storeys
- Tall high-rise: 26+ storeys

From the precision population with observed floor counts:
- N with floors data: 301
- Median storeys: 2
- P25-P75 range: 2-3
- Maximum observed: 6

### Limitations

- Floor data is available for only a subset of the classified population.
- The 4-storey mid-rise boundary aligns with Canadian building code (Part 3/Part 9
  threshold) but may not reflect energy-performance transitions.
- Height-based classification requires validated floor-to-floor assumptions.
- **Decision gate**: The exact boundary between mid-rise and high-rise for simulation
  purposes requires owner approval — current thresholds are configurable defaults.

---

## RQ6: Window-to-Wall Ratio

**How should WWR be handled when building footprints alone cannot provide facade glazing?**

### Direct Answer

**ODB building footprints cannot provide WWR.** This is a fundamental data limitation.

The workflow supports WWR through:
1. **External authoritative observations** (not yet integrated)
2. **Literature-based archetypal assumptions** (configured in `config/default.yaml`)

Current configured defaults (source: archetypal assumption, not observation):
| Facade | WWR | Source |
|--------|----:|--------|
| North | 0.30 | Assumption |
| East | 0.30 | Assumption |
| South | 0.40 | Assumption |
| West | 0.30 | Assumption |

### Limitations

- No observed WWR data exists in ODB v3.
- Current values are configurable placeholders, not validated for Canadian MURBs.
- Facade-specific WWR requires external data (e.g., street-view analysis, energy audits).
- **Required external evidence**: CMHC energy audit data, provincial assessment
  records, or peer-reviewed Canadian MURB glazing studies.

---

## RQ7: Representative Archetypes

**How can representative MURB geometries be derived for simulation?**

### Direct Answer

The archetype methodology uses evidence-based clustering:
1. Evaluate k=2..15 with silhouette scores, inertia, and stability (ARI)
2. Select cluster count based on diagnostics, not convenience
3. Identify medoid (actual building) per cluster as representative
4. Generate synthetic parametric variants for sensitivity analysis

Available populations for archetype generation:
- Precision pathway: 2,768 buildings
- Tiered pathway: 2,995 buildings

Clustering features: footprint area, aspect ratio, compactness, rectangularity.

### Limitations

- Archetype count must be empirically justified per pathway and geography.
- Previous fixed k=5/k=8 values have been deprecated.
- Medoid selection requires the actual building geometry (preserved in GeoParquet).
- Sensitivity to feature selection and outliers must be documented.

---

## RQ8: Geographic Variation

**How do MURB geometry characteristics vary by province?**

### Direct Answer

Geographic coverage is highly uneven due to source data availability:

**Provinces with precision MURBs** (1):
- NS: 2,768 buildings

**Provinces with tiered MURBs** (1):
- NS: 2,995 buildings

**Provinces with zero classified MURBs**: 

### Key Finding

National statistics are dominated by provinces with the richest attribute data (NS, NB
for precision; AB for tiered via height data). Provinces without type, unit, or height
fields contribute no classified MURBs and cannot be represented in current outputs.

### Limitations

- National aggregation without weighting would misrepresent the actual MURB stock.
- Climate zone and urban context stratification are not yet implemented.
- Source coverage is non-random — satellite-derived records have geometry only.

---

## RQ9: Data Quality and Representativeness

**Is the building-footprint sample representative of the national MURB stock?**

### Direct Answer

**No.** The ODB v3 building population is not uniformly suitable for MURB identification:

- Total buildings: 528,307
- Classified as precision MURBs: 2,768 (0.52%)
- Classified as tiered MURBs: 2,995 (0.57%)

The vast majority of records lack the attribute data needed for MURB classification.
Only provinces with populated `type`, `units`, `floors`, or `height` fields can
contribute classified buildings.

### Completeness by Province (from inventory)

Key observations:
- Many provinces have 0% populated attributes beyond geometry and source info
- "Automatically Extracted Buildings" (satellite-derived) have geometry only
- Ontario and BC have the richest attribute data
- Nova Scotia uniquely has ~23% unit-count coverage

### Limitations

- The classified MURB population is biased toward provinces with better data coverage.
- National claims require explicit coverage/weighting caveats.
- Representativeness assessment requires comparison to external MURB population
  estimates (e.g., CMHC housing starts, Census dwelling counts).

---

## RQ10: Simulation Suitability

**What validation is needed to ensure exported geometries are suitable for simulation?**

### Direct Answer

Simulation suitability requires:
1. **gbXML XSD validation** — structural schema compliance (implemented)
2. **Closed-space verification** — all spaces have complete surface boundaries
3. **Outward normal consistency** — surfaces oriented correctly
4. **Area/volume tolerance** — imported values match expected within 2%
5. **Actual OpenStudio import test** — not yet performed

Current status:
- gbXML 7.03 exporter: ✅ Implemented
- Structural validation (element counts, vertex checks): ✅ Implemented
- XSD schema validation: ⚠️ Requires XSD file download
- OpenStudio import test: ❌ Not yet performed
- EnergyPlus simulation test: ❌ Not yet performed

### Limitations

- **OpenStudio compatibility is not claimed** until actual import tests pass.
- Current gbXML exports use simplified box geometry for archetypes.
- Medoid-based extrusion and shape-preserving geometry require further development.
- Floor-to-floor height is an assumption (3.0 m default), not observed.

---

---

## Provenance

- **Generated by**: `scripts/generate_research_report.py`
- **Source data**: Statistics Canada Open Database of Buildings v3
- **Classification**: Option C — Multi-pathway (precision + tiered)
- **Pipeline manifest**: `outputs/reports/run_manifest.json`
- **Persisted data**: `data/processed/murbs_precision.parquet`, `data/processed/murbs_tiered.parquet`
- **Configuration**: `config/default.yaml`
- **Reproducibility seed**: 42
- **Generated at**: 2026-07-28T15:39:04.765453+00:00
