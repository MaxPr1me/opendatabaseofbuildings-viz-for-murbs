# Research Report — Canadian MURB Geometry Analysis

> Generated: 2026-07-30 19:52 UTC
> Source: Statistics Canada Open Database of Buildings v3
> Classification Pathway: Option C — Multi-pathway reporting
> Precision population: 7,623 buildings
> Tiered population: 59,543 buildings
> Provinces processed: 12
> Pipeline manifest: `outputs/reports/run_manifest.json`

---

## RQ1: Building Population and Classification

**How can MURBs be reliably identified from the ODB given heterogeneous source data?**

### Direct Answer

MURBs are identified through an evidence-based classifier applied to the complete ODB v3
population (14,417,429 buildings across 12 provinces), aligned to the
NBC **Part 3** definition (multi-unit residential of 4+ storeys, or > 600 m² building area).
Building `type` is normalized from observed source values via a data-derived mapping
(`config/type_normalization.yaml`, covering English and French/Québec vocabulary). Two
pathways run in parallel (Option C):

- **Precision pathway** (7,623 buildings): storey/unit-verified
  MURBs — an explicit apartment/multi-residential/condominium type corroborated by
  floors ≥ 4 or units ≥ 4 (R001 → confirmed), or floors ≥ 4 (R002) or units ≥ 4 (R003)
  in a residential/unknown context (→ high confidence).
- **Tiered pathway** (59,543 buildings): precision plus probable
  (height ≥ 12 m as a Part 3 storey proxy, R004) and possible candidates (a MURB-intent
  type without storey/unit corroboration, R005; or a large residential footprint
  ≥ 600 m², R006). Explicit low-rise (duplex, semi, townhouse, single-family) and
  non-residential types are excluded up front (R010).

### Population and Method

- **Source**: ODB v3, all 15 GeoPackage files, 12 provinces/territories
- **Total records classified**: 14,417,429
- **Classification**: Rule-based with confidence scores (1.0 → 0.0)
- **No arbitrary row caps**: Complete populations processed

### Evidence Table

| Province | Total | Precision | Tiered | Confirmed | High-Conf | Probable | Possible |
|----------|------:|----------:|-------:|----------:|----------:|---------:|---------:|
| AB | 1,334,404 | 19 | 16,414 | 0 | 19 | 12,127 | 4,268 |
| BC | 1,303,603 | 482 | 10,163 | 192 | 290 | 4,064 | 5,617 |
| MB | 656,775 | 0 | 0 | 0 | 0 | 0 | 0 |
| NB | 661,827 | 2,498 | 3,979 | 1,603 | 895 | 98 | 1,383 |
| NL | 187,694 | 0 | 0 | 0 | 0 | 0 | 0 |
| NS | 528,307 | 2,671 | 2,888 | 189 | 2,482 | 0 | 217 |
| NT | 11,811 | 0 | 72 | 0 | 0 | 0 | 72 |
| ON | 5,695,485 | 1,953 | 23,478 | 1,027 | 926 | 14,237 | 7,288 |
| PE | 85,856 | 0 | 0 | 0 | 0 | 0 | 0 |
| QC | 3,679,721 | 0 | 2,549 | 0 | 0 | 0 | 2,549 |
| SK | 259,461 | 0 | 0 | 0 | 0 | 0 | 0 |
| YT | 12,485 | 0 | 0 | 0 | 0 | 0 | 0 |

### Limitations

- Provinces with no classified MURBs in this run: MB, NL, PE, SK, YT — they
  lack populated `type`, `floors`, and `units` fields.
- Quebec has type data (French vocabulary, now recognized) but no storey/unit fields and no
  explicit apartment types, so it contributes only weak `possible` candidates via
  large-footprint residential (R006); most QC records resolve to `insufficient_information`
  rather than being dropped.
- Under the Part 3 definition, generic 'Residential' does not confirm a MURB without
  storey/unit evidence — the precision pathway therefore has high confidence but low
  geographic coverage (AB, BC, NB, NS, ON).

---

## RQ2: Typical MURB Size

**What are defensible statistical distributions for Canadian MURB footprint area,
storeys, height, unit count, and dimensions?**

### Direct Answer

Based on the precision pathway (7,623 buildings from AB, BC, NB, NS, ON
with storey/unit-verified multi-unit evidence):

| Metric | N | Min | P25 | Median | P75 | Max | Mean | Std | Missing |
|--------|--:|----:|----:|-------:|----:|----:|-----:|----:|--------:|
| Footprint area (m²) | 7,623 | 4.7 | 213.8 | 419.5 | 915.5 | 14,803.4 | 727.2 | 889.6 | 0.0% |
| MRR length (m) | 7,623 | 3.7 | 19.4 | 29.8 | 49.9 | 240.4 | 38.5 | 26.0 | 0.0% |
| MRR width (m) | 7,623 | 1.0 | 11.6 | 15.9 | 22.3 | 150.6 | 19.3 | 12.2 | 0.0% |
| Storeys | 2,180 | 1.0 | 3.0 | 4.0 | 6.0 | 45.0 | 5.1 | 4.3 | 0.0% |
| Dwelling units | 6,862 | 1.0 | 5.0 | 9.0 | 25.0 | 583.0 | 23.7 | 35.9 | 0.0% |

**Tiered pathway** (59,543 buildings — broader candidate population):

| Metric | N | Min | P25 | Median | P75 | Max | Mean | Std | Missing |
|--------|--:|----:|----:|-------:|----:|----:|-----:|----:|--------:|
| Footprint area (m²) | 59,543 | 4.3 | 227.0 | 451.2 | 949.5 | 162,819.8 | 919.0 | 2,424.9 | 0.0% |
| MRR length (m) | 59,543 | 2.5 | 20.0 | 31.4 | 51.2 | 589.0 | 40.4 | 31.2 | 0.0% |
| MRR width (m) | 59,543 | 1.0 | 12.6 | 16.6 | 24.5 | 437.2 | 21.5 | 16.8 | 0.0% |
| Storeys | 6,085 | 1.0 | 2.0 | 2.0 | 3.0 | 45.0 | 3.0 | 3.1 | 0.0% |
| Dwelling units | 10,612 | 1.0 | 2.0 | 4.0 | 13.0 | 583.0 | 15.9 | 30.8 | 0.0% |

### Recommended Simulation Ranges (Precision Pathway)

| Parameter | Minimum (P5) | Central (Median) | Maximum (P95) | Source |
|-----------|-------------:|-----------------:|--------------:|--------|
| Footprint area (m²) | 117.2 | 419.5 | 2,235.6 | Observed |
| Storeys | 1 | 4 | 14 | Observed |
| Units | 4 | 9 | 92 | Observed |

### Limitations

- Floor/unit counts are available only for the provinces with precision MURBs
  (AB, BC, NB, NS, ON).
- Height data is sparse and not available from all sources.
- Footprint ≠ floor plate — podiums, setbacks, and additions are not captured.
- GFA cannot be reliably computed without confirmed storey counts.

---

## RQ3: Building Form and Aspect Ratio

**What are the characteristic geometric properties of Canadian MURBs?**

### Direct Answer

| Metric | N | Min | P25 | Median | P75 | Max | Mean | Std | Missing |
|--------|--:|----:|----:|-------:|----:|----:|-----:|----:|--------:|
| Aspect ratio | 7,623 | 1.0 | 1.4 | 1.8 | 2.5 | 21.9 | 2.1 | 1.0 | 0.0% |
| Compactness (Polsby-Popper) | 7,623 | 0.0 | 0.5 | 0.6 | 0.7 | 1.0 | 0.6 | 0.1 | 0.0% |
| Rectangularity | 7,623 | 0.2 | 0.8 | 0.9 | 1.0 | 1.0 | 0.9 | 0.1 | 0.0% |
| Convexity | 7,623 | 0.2 | 0.9 | 1.0 | 1.0 | 1.0 | 0.9 | 0.1 | 0.0% |
| Orientation (deg from N) | 7,623 | 0.1 | 46.4 | 87.7 | 134.5 | 179.9 | 87.8 | 50.2 | 0.0% |
| Perimeter (m) | 7,623 | 10.2 | 63.8 | 94.0 | 151.3 | 1,138.5 | 119.8 | 79.0 | 0.0% |

### Key Findings

- Median aspect ratio of ~1.8 indicates
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
- Rectangularity: median = 0.920, P25 = 0.815
- Convexity: median = 0.958, P25 = 0.895

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
- N with floors data: 2,180
- Median storeys: 4
- P25-P75 range: 3-6
- Maximum observed: 45

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
- Precision pathway: 7,623 buildings
- Tiered pathway: 59,543 buildings

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

**Provinces with precision MURBs** (5):
- NS: 2,671 buildings
- NB: 2,498 buildings
- ON: 1,953 buildings
- BC: 482 buildings
- AB: 19 buildings

**Provinces with tiered MURBs** (7):
- ON: 23,478 buildings
- AB: 16,414 buildings
- BC: 10,163 buildings
- NB: 3,979 buildings
- NS: 2,888 buildings
- QC: 2,549 buildings
- NT: 72 buildings

**Provinces with zero classified MURBs**: MB, NL, PE, SK, YT

### Key Finding

National statistics are dominated by provinces with the richest attribute data — those with
observed storey or unit counts drive the precision pathway, while provinces with height data
(e.g., AB and ON) add probable candidates to the tiered pathway via the height proxy. Provinces
without type, unit, or height fields contribute no classified MURBs and cannot be represented
in current outputs.

### Limitations

- National aggregation without weighting would misrepresent the actual MURB stock.
- Climate zone and urban context stratification are not yet implemented.
- Source coverage is non-random — satellite-derived records have geometry only.

---

## RQ9: Data Quality and Representativeness

**Is the building-footprint sample representative of the national MURB stock?**

### Direct Answer

**No.** The ODB v3 building population is not uniformly suitable for MURB identification:

- Total buildings: 14,417,429
- Classified as precision MURBs: 7,623 (0.05%)
- Classified as tiered MURBs: 59,543 (0.41%)

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
- **Generated at**: 2026-07-30T19:52:20.456543+00:00
