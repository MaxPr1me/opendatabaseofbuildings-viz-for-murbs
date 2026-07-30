# Known Limitations

## Data Limitations

1. **Footprint ≠ floor plate**: Ground-level footprints may include podiums, garages, additions, and overhangs that differ from typical upper-floor plates.

2. **No window information**: Building footprints do not contain facade glazing data. WWR must come from external sources or archetypal assumptions.

3. **Incomplete storey data**: Only 0–9% of records have storey counts, varying by province.

4. **Incomplete height data**: Only 0–27% of records have height values.

5. **Sparse unit counts**: Only 0–23% of records have dwelling unit information.

6. **Non-random coverage**: Open-data availability depends on municipal open-data policies. Data-rich municipalities will dominate unweighted statistics.

7. **Source heterogeneity**: Building-type classifications are source-specific and not nationally standardized.

8. **Temporal inconsistency**: Sources have different update dates. Some footprints may represent demolished buildings.

9. **Text-encoded numerics**: All attributes are stored as TEXT, requiring careful parsing and missing-value handling.

10. **Satellite-derived footprints**: "Automatically Extracted Buildings" have geometry only—no attributes.

11. **Type establishes MURB status only rarely**: The `type` field is normalized via a
    data-derived mapping ([config/type_normalization.yaml](../config/type_normalization.yaml),
    generated from the full-population schema audit and covering English and French/Québec
    vocabulary). However, under the NBC Part 3 definition only explicit
    apartment/multi-residential/condominium values are positive MURB evidence from type alone
    — and only ~0.7% of typed records carry those. Generic values (e.g. `Residential`,
    `Résidence`) are context only and require storey/unit/height evidence to classify. Values
    the mapping cannot categorize resolve to `insufficient_information` (surfaced, not dropped).

## Methodological Limitations

1. **MURB identification**: Cannot reliably identify all MURBs from footprint data alone without external evidence.

2. **National representativeness**: Unweighted national statistics may not reflect the true distribution of Canadian MURBs.

3. **Shape classification**: Automated classification has inherent uncertainty, especially for complex or articulated forms.

4. **Archetype generalization**: Any representative geometry simplifies real building diversity.

5. **Polygon averaging**: Averaging coordinates from unrelated buildings produces meaningless geometry.

6. **Simulation fidelity**: Extruded footprints are a simplification of actual 3D building forms.

7. **Classification coverage bias (attribute sparsity)**: Under the NBC Part 3 definition
    (4+ storeys, or > 600 m² building area), MURB confirmation depends on storey and unit
    fields that are absent for most provinces (`floors` 0–9%, `units` 0–23%). Quebec, Manitoba,
    Newfoundland, PEI, Saskatchewan, and Yukon have essentially no storey/unit data and no
    explicit apartment-type values, so they contribute few or only weak (`possible`) MURBs.
    The classified population is dominated by Ontario, BC, Nova Scotia, New Brunswick, and
    Alberta. Records lacking evidence are reported as `insufficient_information`, not dropped,
    and any national statistic must be reported with this bias stated.

## Technical Limitations

1. **Memory**: National dataset (~14.4M records) cannot be loaded simultaneously; province-level processing required.

2. **Processing time**: Full national pipeline will require significant computation time.

3. **gbXML complexity**: Validated gbXML suitable for simulation requires careful engineering beyond simple XML generation.
