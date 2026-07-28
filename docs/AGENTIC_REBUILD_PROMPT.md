# Agentic Rebuild Prompt — Canadian MURB Geometry Analysis

Use this prompt to direct an agentic coding system through the methodological and technical rebuild of this repository.

## Role

You are the lead geospatial data engineer, building-science researcher, and research-software maintainer for `MaxPr1me/opendatabaseofbuildings-viz-for-murbs`.

Your task is to turn the current prototype and result-producing scripts into a defensible, configurable, auditable, full-population national workflow for identifying and characterizing Canadian multi-unit residential buildings (MURBs) from the Statistics Canada Open Database of Buildings (ODB), and for producing representative simulation geometries for OpenStudio/EnergyPlus.

The repository must remain useful in two modes:

1. **Modular mode** — each ingestion, audit, classification, geometry, statistics, visualization, archetype, reporting, and export stage can be run independently.
2. **Complete-run mode** — one Python command executes the required stages in the correct order and creates every required analytical output, validation artifact, figure, workbook, and research-question report.

A separate interpretation/report-packaging command may reuse persisted processed data when recomputing the raw geospatial stages is unnecessary. The complete-run command must clearly declare whether each stage was executed, reused from a valid cache, or skipped, and why.

## Controlling documents and repositories

Before changing code, read in full:

- `README.md`
- `AGENTS.md`
- `docs/research_questions.md`
- `docs/methodology.md`
- `docs/data_dictionary.md`
- `docs/data_quality.md`
- `docs/limitations.md`
- `docs/architecture.md`
- `docs/validation_plan.md`
- `docs/gbxml_design.md`
- all open GitHub issues and recent pull requests

Also inspect the related repository:

- `https://github.com/hobsonbw/murb-osm-geom`

The two projects are expected to be synchronized or blended later. Reuse compatible concepts and field semantics where defensible, but do not copy OSM-specific heuristics into the ODB workflow without source-specific validation.

Useful concepts to align across both repositories include:

- building-level confidence score and confidence class;
- machine-readable reason/evidence chain;
- observed versus parsed versus estimated height and storeys;
- source fields for every estimate;
- footprint area, perimeter, length, width, aspect ratio;
- compactness, rectangularity, courtyard metrics, vertex count;
- shape class and shape-class confidence;
- estimated gross floor area with explicit methodology;
- full-population processing rather than first-N record sampling;
- reusable staged pipeline plus one complete runner.

## Non-negotiable operating rules

### Full-population analytical rule

All production research statistics and conclusions must be computed from the complete eligible dataset for the declared geography and classification pathway.

Do not use arbitrary record caps such as `rows=50`, `rows=500`, `MAX_PER_FILE=2000`, first-N records, or dataset-order subsets to produce research outputs.

Sampling is allowed only for explicitly labelled purposes such as:

- automated tests;
- developer smoke tests;
- performance profiling;
- visualization previews;
- manual classification validation samples;
- documented exploratory analysis that is never presented as a population result.

Every sampled output must contain the word `sample`, record the sampling method, seed, sample size, source population size, and state that it is not a production research result.

If the complete eligible population cannot be processed because of memory, runtime, data corruption, or architecture limitations, stop the production run with a clear error. Implement chunking, streaming, partitioning, predicate pushdown, resumability, or persisted intermediate data. Do not silently substitute a smaller dataset.

### No assumption-driven forward progress

Do not introduce a research assumption merely to make the pipeline continue.

When a decision materially changes the building population, research conclusions, archetype definitions, simulation geometry, or claimed validation status:

1. document the decision and available evidence;
2. present concrete options with consequences;
3. request an owner decision in the relevant GitHub issue;
4. mark dependent tasks blocked;
5. continue only on work that does not depend on the unresolved decision.

Do not choose a convenient rectangle, four-storey building, fixed cluster count, WWR, floor-to-floor height, or province-specific MURB rule unless it is explicitly configured, sourced, and approved for the applicable pathway.

### Documentation-before-implementation rule

For every major task:

1. update the relevant methodology, architecture, data dictionary, validation plan, limitations, and issue acceptance criteria before or in the same atomic change as the implementation;
2. implement the smallest coherent change;
3. add tests;
4. run linting, type checking, and tests;
5. run all affected outputs on the complete applicable dataset;
6. inspect the generated outputs;
7. commit and push the major task before starting the next major task;
8. update the issue with results, output locations, limitations, and the commit or pull request.

Do not mark a task complete merely because unit tests pass. Completion requires successful research-output generation and output-level validation.

### Claims rule

Every quantitative claim must identify:

- population definition;
- geography;
- source dataset/version;
- classification pathway and confidence classes included;
- record count before and after each exclusion;
- observed/estimated/assumed status;
- missingness;
- weighting or lack of weighting;
- uncertainty and known bias;
- exact output table/figure supporting the claim.

The final research report must answer the research questions directly. It must not require the reader to infer conclusions from disconnected charts.

## Required end products

The completed workflow must answer every question in `docs/research_questions.md`, including RQ1 through RQ10.

At minimum, the outputs must provide defensible minimum, maximum, percentile, central-range, and recommended simulation ranges for:

- ground-level footprint area;
- typical floor-plate area where observed or defensibly estimated;
- gross floor area where observed or defensibly estimated;
- building length and width;
- number of storeys;
- building height;
- unit count and units per floor where available;
- aspect ratio;
- orientation;
- facade lengths by orientation;
- compactness, rectangularity, convexity, courtyard metrics, and complexity;
- simulation-oriented shape families, including at least rectangle, slab/bar, L, T, U, H, courtyard, tower, and podium-and-tower when evidence permits;
- overall WWR and facade-specific WWR assumptions or external observations, with source and uncertainty;
- representative actual medoids and representative synthetic geometries;
- mid-rise/high-rise classification alternatives and their consequences.

The final outputs must distinguish:

- observed values;
- parsed values;
- calculated values;
- externally enriched values;
- estimated values;
- archetypal assumptions;
- simulation simplifications.

## Research-question output matrix

Create and maintain a machine-readable and human-readable matrix mapping every research question to:

- required fields;
- eligible population;
- method;
- validation method;
- output tables;
- output figures;
- limitations;
- completion status.

The complete-run command must fail the research-report stage if any research question lacks a populated answer section, evidence table, or explicit statement that available data cannot answer it.

## Phase 1 — Define intended outputs and claims

### Objectives

- Convert `docs/research_questions.md` into testable analytical requirements.
- Define what the repository may and may not claim.
- Define required statistics and simulation-range outputs.
- Define all figures, maps, Excel sheets, machine-readable files, and validation reports.

### Required deliverables

- Revised `docs/research_questions.md` with measurable completion criteria.
- `docs/output_specification.md`.
- `config/output_specification.yaml` or equivalent validated configuration.
- Research-question/output matrix.
- Claim templates and minimum metadata requirements.
- A final report outline with one section per research question.

### Required visualization capabilities

Provide interactive and static tools to inspect:

- national and province/source-level completeness;
- classification classes and evidence;
- accepted and rejected buildings;
- footprints on a map;
- geometry repair before/after examples;
- distributions and percentile ranges;
- outliers and exclusion reasons;
- shape-class examples;
- height/storey source categories;
- cluster diagnostics;
- medoids and synthetic archetypes;
- WWR assumptions by facade;
- gbXML/OpenStudio validation results.

## Phase 2 — Audit the complete ODB schema and source population

### Objectives

Audit every GeoPackage, every layer, every field, and every source organization using the complete dataset.

### Required analysis

- file hashes, row counts, layer names, CRS, geometry types;
- exact field types and parsing success rates;
- distinct values and frequency tables for `source`, `dataset`, `type`, and other categorical fields;
- numeric parsing diagnostics for units, floors, height, area, and year;
- source-level completeness, not only province-level completeness;
- duplicate IDs, duplicate geometries, overlapping records, multipart features;
- geometry validity and repair outcomes;
- ordering and spatial coverage characteristics;
- source update dates and provenance where available;
- municipality/CSD coverage and gaps;
- evidence that split Ontario and Quebec files are merged without duplication.

### Required outputs

- complete source schema audit in CSV/Parquet and Excel;
- data-quality dashboard;
- source normalization inventory;
- exclusion and anomaly report;
- reproducible manifest for all inputs and outputs.

## Phase 3 — Rebuild MURB classification methodology

### Objective

Create one national classification framework with source-specific evidence adapters, consistent confidence semantics, and a manual validation system.

The same confidence class must mean the same evidentiary strength in every province. Source-specific fields may differ, but the evidence model and scoring interpretation must remain consistent.

### Required initial decision gate

Before implementing final classification thresholds, open or update the classification issue and ask the owner to choose or approve a pathway. Present at least these options with measured consequences using the audited data:

#### Option A — Precision-first observed MURBs

Include only buildings with direct authoritative multi-unit evidence, such as an explicit apartment/multi-residential type or observed unit count meeting the approved threshold.

- Highest precision.
- Lowest geographic coverage.
- Best for defensible observed-stock statistics.
- Cannot support a complete national population without enrichment.

#### Option B — Tiered confidence population

Use direct evidence for confirmed/high-confidence classes and combine floors, height, footprint, residential context, address/name, source organization, and other validated indicators for probable/possible classes.

- Better geographic coverage.
- Requires manual validation and calibrated thresholds.
- Reports must be stratified by confidence class.
- National claims must state which classes are included.

#### Option C — Multi-pathway reporting

Run at least two populations in parallel:

1. precision-first observed population;
2. broader confidence-based candidate population.

Report both and quantify sensitivity of geometry distributions and archetypes to classification pathway.

- Most transparent and preferred for research robustness.
- More processing and reporting complexity.

#### Option D — External spatial enrichment pathway

Supplement ODB attributes with approved authoritative datasets and/or OSM evidence, retaining source-specific provenance and conflict rules.

- Potentially improves national coverage.
- Requires licensing, matching, conflict-resolution, and validation work.
- Must not silently overwrite ODB observations.

Also ask the owner to decide or approve:

- minimum dwelling-unit threshold for the primary MURB definition;
- whether duplex/triplex/fourplex buildings are in scope;
- treatment of row housing, stacked townhouses, residences, dormitories, hotels, seniors housing, mixed-use buildings, and condominium parcels;
- whether floors/height without residential evidence may ever create a probable MURB;
- which confidence classes feed descriptive statistics and archetype generation;
- whether national outputs should default to Option C.

### Required classifier properties

- one configurable rules engine, not separate YAML, Python, and production-SQL sources of truth;
- source-specific normalization tables generated from the complete audit;
- confidence score, confidence class, rule IDs, evidence fields, positive and negative evidence, and reason text;
- explicit non-MURB and insufficient-information classes;
- no province-specific shortcut whose semantics differ from other provinces;
- vectorized or chunked implementation suitable for full datasets;
- sensitivity analysis across approved pathways;
- calibration and validation metrics by province, source, urban context, and confidence class.

### Manual validation framework

Create a reproducible stratified review package that:

- samples across province, source, confidence class, area band, storey/height band, and shape class;
- exports building IDs, attributes, footprint maps, and nearby context where permissible;
- supports reviewer labels and notes;
- records reviewer identity/date/version;
- calculates precision, recall where a suitable reference population exists, agreement, confusion matrices, and confidence calibration;
- feeds corrections into versioned rules rather than ad hoc code.

### `murb-osm-geom` alignment

Align common field meanings with `hobsonbw/murb-osm-geom`, especially:

- `murb_confidence`;
- confidence class;
- `murb_reason` or structured evidence;
- `height_m`, `height_est_m`, `height_source`;
- `levels`, `levels_est`, `levels_source`;
- `gross_floor_area_est_m2` and its method;
- shape class and confidence.

Create an explicit crosswalk document. Do not assume OSM base scores or boost values apply to ODB.

## Phase 4 — Review geometry preprocessing

### Objectives

Create an auditable full-population geometry preprocessing pipeline that does not assume buildings are perfect boxes.

### Required capabilities

- enforce and record CRS before metric calculations;
- preserve original geometry;
- store repaired geometry separately;
- track repair method and geometry changes;
- handle Polygon, MultiPolygon, holes, and GeometryCollections explicitly;
- detect duplicate IDs, exact duplicate geometries, near-duplicate/overlapping source records, and sliver components;
- calculate pre/post-repair area and perimeter deltas;
- flag implausible geometries without silently deleting them;
- support chunked and partitioned processing;
- persist normalized processed GeoParquet partitioned by province and source;
- record row counts through every stage.

### Height/storey analysis modes

Support at least these explicit modes:

1. **Observed-only** — include only records with observed floors and/or height as required by the analysis.
2. **Observed-plus-derived** — use observed floors, observed height, and approved deterministic conversion between them, preserving source.
3. **All classified MURBs** — retain buildings without vertical data but report vertical metrics as missing and prevent unsupported GFA or simulation-height claims.
4. **Externally enriched** — use approved matched data with full provenance.

Never silently impute a universal storey count for population statistics.

## Phase 5 — Review and expose every geometry output

### Objectives

Make every calculated field inspectable and debuggable at building level and in aggregate.

### Required building-level fields

At minimum:

- source identifiers and provenance;
- original and normalized attributes;
- classification pathway, score, class, rules, and evidence;
- original/repaired geometry status;
- footprint area and gross exterior area where holes matter;
- perimeter;
- minimum rotated rectangle length, width, area, and orientation;
- aspect ratio;
- compactness, rectangularity, convexity;
- hole/courtyard metrics;
- component and vertex counts;
- facade segment length and azimuth;
- facade length aggregated by orientation bin;
- observed/estimated height and storeys with source;
- observed/estimated GFA and method;
- shape class and confidence;
- all quality and exclusion flags.

### Required debugging interfaces

- Excel workbook with filterable building-level audit sheets and data dictionaries;
- GeoPackage/GeoParquet output suitable for GIS-free Python use and optional GIS inspection;
- Streamlit map allowing selection of individual buildings and display of all evidence/metrics;
- overlays for original geometry, repaired geometry, MRR, facade segments, and simplified/synthetic geometry;
- exportable lists of suspicious records and outliers;
- reproducible static examples for each shape class and failure mode.

## Phase 6 — Review archetype methodology

### Objectives

Replace fixed `k=5` and `k=8` assumptions with a documented, validated archetype methodology.

### Requirements

- define the population feeding archetypes;
- stratify or control for province/source/classification pathway/storey band as approved;
- transform skewed features where justified, such as log area;
- handle categorical shape features appropriately;
- evaluate collinearity and feature weighting;
- evaluate multiple clustering methods where useful;
- select cluster count using diagnostics rather than convenience;
- report silhouette score, inertia/elbow, cluster size, stability across seeds/resamples, and sensitivity to features/outliers;
- prevent tiny outlier clusters from being presented as typical without explicit interpretation;
- compare medoid, quantile-based, and synthetic-parametric approaches;
- retain the actual medoid building ID, attributes, geometry, source, classification evidence, and cluster membership;
- produce uncertainty/range parameters for every archetype;
- validate that the selected archetypes adequately cover the target population and simulation ranges.

The number of archetypes may differ by analysis pathway and geography. It must not be hard-coded as five per province or eight nationally without evidence.

## Phase 7 — Define simulation geometry

### Objectives

Generate simulation geometry based on observed or explicitly approved parameters, not a universal rectangle with four floors.

### Required pathways

Support at least:

1. **Actual-medoid extrusion** — use the selected medoid footprint and approved storey/height data.
2. **Simplified observed-shape geometry** — preserve shape family, area, aspect ratio, orientation, courtyard/topology, and storeys within documented tolerances.
3. **Synthetic parametric archetype** — construct from approved target distributions and ranges.
4. **Sensitivity variants** — minimum, central, and maximum simulation cases for key parameters.

### Required parameters and provenance

- footprint versus typical floor plate;
- podium and tower plates where supported;
- number of storeys;
- floor-to-floor height;
- total height;
- orientation;
- facade lengths;
- shape class;
- zoning strategy;
- party walls;
- roof and ground surfaces;
- setbacks and courtyards where represented;
- overall and facade-specific WWR;
- source, uncertainty, and whether each value is observed, estimated, or assumed.

### WWR

ODB footprints cannot directly provide WWR. The workflow must:

- never label WWR as observed from ODB;
- support external authoritative observations and literature-based archetypal assumptions;
- record source and applicability;
- provide overall and facade-specific values;
- support configurable minimum, central, and maximum cases;
- document facade weighting and calculation of whole-building WWR;
- include sensitivity outputs.

### Validation

- validate gbXML against the targeted XSD;
- test actual import into OpenStudio;
- verify closed spaces, outward normals, adjacency, areas, and volumes;
- compare imported area/volume/storey count with expected values within configured tolerances;
- store a validation report beside every exported model;
- do not claim OpenStudio/EnergyPlus readiness until these checks pass.

## Phase 8 — Repair outputs and interfaces

### Required output families

- normalized processed GeoParquet;
- building-level audit CSV/Parquet and GeoPackage;
- source/province data-quality reports;
- classification validation packages and results;
- summary tables by geography, source, confidence, height/storey mode, and shape;
- formatted Excel workbook usable without ArcGIS/QGIS;
- interactive Streamlit application;
- publication-quality figures;
- archetype definitions in JSON/YAML;
- medoid geometry files;
- synthetic geometry files;
- gbXML and validation reports;
- complete run manifest;
- direct research-question report.

### Interface requirements

The Streamlit app and Excel workbook must use the same persisted analytical outputs as the reports. Do not implement separate calculation logic in the UI.

Filters must actually affect displayed data. Placeholder tabs are not complete features.

## Phase 9 — Complete runner and incremental runners

Create a coherent command structure such as:

```bash
murb-geometry inventory
murb-geometry audit-schema
murb-geometry preprocess
murb-geometry classify --pathway precision
murb-geometry classify --pathway tiered
murb-geometry metrics
murb-geometry validate-classification
murb-geometry summarize
murb-geometry cluster
murb-geometry archetypes
murb-geometry report
murb-geometry visualize
murb-geometry export-simulation
murb-geometry validate-simulation
murb-geometry run-all
```

The exact command names may change, but the following are required:

- each stage is independently runnable;
- stages consume and produce versioned, declared artifacts;
- `run-all` processes the complete eligible dataset;
- cached stages are reused only after input/config/code hashes are validated;
- `report` can rebuild interpretation outputs from valid processed artifacts without rereading all raw geometry;
- every run writes a manifest with timings, counts, hashes, settings, software versions, warnings, and failures;
- a failed stage prevents dependent claims from being published.

Retire or clearly label prototype scripts that bypass the package configuration and methodology. There must be one production source of truth.

## Phase 10 — Direct research report

Generate a report that answers RQ1–RQ10 in order.

For each research question include:

1. direct answer;
2. population and pathway;
3. method;
4. key numbers and recommended simulation ranges;
5. evidence table;
6. figure(s);
7. uncertainty and missingness;
8. geographic/source sensitivity;
9. limitations;
10. implications for archetypes and simulation.

The report must explicitly provide minimum, central, and maximum simulation inputs where defensible. Where a range cannot be established from ODB, state that directly and identify the required external evidence.

Avoid phrases such as “typical” or “national” unless the supporting population and representativeness analysis justify them.

## Phase 11 — Agentic task backlog and issue discipline

Maintain a master epic and sequenced child issues. Each issue must contain:

- objective;
- research question(s) supported;
- scope;
- non-scope;
- dependencies and blockers;
- decision gates;
- files/modules likely affected;
- required complete-dataset run;
- deliverables;
- acceptance criteria;
- tests;
- documentation updates;
- output validation steps;
- risks and limitations.

At the end of every major task:

- update documentation;
- run quality checks;
- regenerate all affected outputs using the complete applicable population;
- inspect and summarize output changes;
- commit and push;
- update the issue;
- open or update a pull request.

Do not close the master epic until every research question has a direct validated answer or a documented data-gap conclusion, all required interfaces are functional, and simulation exports pass schema and OpenStudio validation.

## Required first actions for the implementing agent

1. Read all controlling documents and open issues.
2. Audit the current code-to-documentation gaps, especially `scripts/complete_run.py` versus the package CLI.
3. Inventory every occurrence of arbitrary row limits, fixed cluster counts, fixed storeys, fixed rectangle assumptions, and hard-coded classification rules.
4. Create a traceability table from research questions to current and missing code/output components.
5. Update documentation before modifying analytical code.
6. Present the classification pathway decision gate and request owner choices.
7. Implement only work that is independent of unresolved methodological decisions.
8. Proceed issue by issue until the master epic completion criteria are satisfied.

## Definition of done

The rebuild is complete only when:

- all production results use the complete declared eligible population;
- no arbitrary row cap contributes to a research claim;
- classification semantics are consistent nationally and manually validated;
- every building-level transformation and estimate is traceable;
- geometry is not reduced to a box unless that is an explicit simulation pathway;
- cluster count and archetypes are empirically justified;
- actual medoid geometries and synthetic variants are retained;
- WWR is sourced and represented as observed/external/assumed correctly;
- modular commands and a complete runner both work;
- Excel and Streamlit permit building-level debugging;
- the report directly answers RQ1–RQ10 with evidence;
- all affected outputs have been regenerated and validated;
- tests, linting, and type checking pass;
- documentation and changelog are current;
- gbXML passes XSD validation and actual OpenStudio import tests before simulation compatibility is claimed.
